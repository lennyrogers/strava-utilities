#!/usr/bin/env python3
import os
import sys
import time
import json
import random
import datetime as dt
from typing import Dict, List, Tuple, Optional

import requests

BASE_API = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"
PROGRESS_FILE = "unstar_progress.json"


class StravaError(RuntimeError):
    pass


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> Tuple[str, str]:
    """Refresh access token using Strava OAuth refresh_token grant."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise StravaError(f"Token refresh failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    # Strava may rotate refresh tokens; keep the new one if present
    return data["access_token"], data.get("refresh_token", refresh_token)


def auth_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _seconds_until_next_quarter_hour_utc() -> float:
    """Strava resets 15-min limits at :00, :15, :30, :45 (natural 15-min intervals)."""
    now = dt.datetime.utcnow()
    minute = now.minute
    next_q = ((minute // 15) + 1) * 15
    if next_q == 60:
        next_time = now.replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_q, second=0, microsecond=0)
    return max(0.0, (next_time - now).total_seconds())


def _parse_pair(header_val: Optional[str]) -> Optional[Tuple[int, int]]:
    if not header_val:
        return None
    a, b = header_val.split(",")
    return int(a), int(b)


def _rate_meta(resp: requests.Response) -> Dict[str, Optional[Tuple[int, int]]]:
    # Per Strava docs, these headers are returned with every API request. [2](https://markaicode.com/python-api-rate-limit-exponential-backoff/)
    return {
        "read_limit": _parse_pair(resp.headers.get("X-ReadRateLimit-Limit")),
        "read_usage": _parse_pair(resp.headers.get("X-ReadRateLimit-Usage")),
        "limit": _parse_pair(resp.headers.get("X-RateLimit-Limit")),
        "usage": _parse_pair(resp.headers.get("X-RateLimit-Usage")),
        "retry_after": resp.headers.get("Retry-After"),
    }


def request_with_throttle(method: str, path: str, *, access_token: str, **kwargs) -> requests.Response:
    """Request wrapper that throttles based on Strava rate-limit headers and handles 429."""
    url = f"{BASE_API}{path}"
    headers = kwargs.pop("headers", {})
    headers.update(auth_headers(access_token))
    kwargs["headers"] = headers

    max_attempts = 8
    for attempt in range(1, max_attempts + 1):
        resp = requests.request(method, url, timeout=30, **kwargs)
        meta = _rate_meta(resp)

        # Proactive throttle if close to the 15-min READ limit
        if meta["read_limit"] and meta["read_usage"]:
            limit15, _ = meta["read_limit"]
            used15, _ = meta["read_usage"]
            # If within 3 requests of limit, pause to next window + jitter
            if used15 >= limit15 - 3:
                sleep_s = _seconds_until_next_quarter_hour_utc() + random.uniform(1.0, 5.0)
                print(f"[throttle] Read usage {used15}/{limit15}. Sleeping {sleep_s:.1f}s")
                time.sleep(sleep_s)

        if resp.status_code != 429:
            return resp

        # 429 handling: wait Retry-After if present else next 15-min boundary
        if meta["retry_after"]:
            wait_s = int(meta["retry_after"])
        else:
            wait_s = int(_seconds_until_next_quarter_hour_utc() + random.uniform(1.0, 10.0))

        print(f"[429] Rate limited. Waiting {wait_s}s (attempt {attempt}/{max_attempts})")
        time.sleep(wait_s)

    raise StravaError(f"Repeated 429 responses calling {path}. Aborting.")


def list_starred_segments(access_token: str, per_page: int = 200) -> List[dict]:
    """Fetch all starred segments via pagination."""
    all_segments: List[dict] = []
    page = 1

    while True:
        resp = request_with_throttle(
            "GET",
            "/segments/starred",
            access_token=access_token,
            params={"page": page, "per_page": per_page},
        )
        if resp.status_code != 200:
            raise StravaError(f"Failed listing starred segments ({resp.status_code}): {resp.text}")

        batch = resp.json()
        if not batch:
            break

        all_segments.extend(batch)
        print(f"[list] page={page} fetched={len(batch)} total={len(all_segments)}")
        page += 1

    return all_segments


def unstar_segment(access_token: str, segment_id: int) -> None:
    """Unstar a single segment."""
    resp = request_with_throttle(
        "PUT",
        f"/segments/{segment_id}/starred",
        access_token=access_token,
        headers={"Content-Type": "application/json"},
        data=json.dumps({"starred": False}),
    )
    if resp.status_code != 200:
        raise StravaError(f"Unstar failed for {segment_id} ({resp.status_code}): {resp.text}")


def load_progress() -> Dict[str, object]:
    if not os.path.exists(PROGRESS_FILE):
        return {"done_ids": []}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(done_ids: List[int]) -> None:
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"done_ids": done_ids}, f, indent=2)


def main() -> int:
    client_id = _env("STRAVA_CLIENT_ID")
    client_secret = _env("STRAVA_CLIENT_SECRET")
    refresh_token = _env("STRAVA_REFRESH_TOKEN")
    access_token = _env("STRAVA_ACCESS_TOKEN")

    # Prefer refresh flow if available
    if refresh_token:
        if not (client_id and client_secret):
            raise StravaError("STRAVA_REFRESH_TOKEN provided but STRAVA_CLIENT_ID/SECRET missing.")
        access_token, new_refresh = refresh_access_token(client_id, client_secret, refresh_token)
        if new_refresh != refresh_token:
            print("NOTE: Strava rotated refresh token. Update STRAVA_REFRESH_TOKEN in your env.")
            # don't print token value
    elif not access_token:
        raise StravaError("Set STRAVA_REFRESH_TOKEN (preferred) or STRAVA_ACCESS_TOKEN.")

    progress = load_progress()
    done_ids = set(progress.get("done_ids", []))

    starred = list_starred_segments(access_token)
    ids = [int(seg["id"]) for seg in starred if "id" in seg]

    print(f"[start] starred_segments={len(ids)} already_done={len(done_ids)}")

    completed: List[int] = list(done_ids)
    for i, seg_id in enumerate(ids, start=1):
        if seg_id in done_ids:
            continue
        try:
            unstar_segment(access_token, seg_id)
            completed.append(seg_id)
            done_ids.add(seg_id)
            if i % 10 == 0:
                save_progress(completed)
            print(f"[ok] {i}/{len(ids)} unstarred {seg_id}")
            # small steady pacing helps reduce burstiness even before headers force it
            time.sleep(0.2)
        except StravaError as e:
            save_progress(completed)
            print(f"[error] {e}", file=sys.stderr)
            return 2

    save_progress(completed)
    print("[done] All segments unstarred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())