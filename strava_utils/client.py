"""
Strava API Client

Main client for interacting with the Strava API.
"""

import os
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from .auth import StravaAuth

logger = logging.getLogger(__name__)


class StravaClient:
    """
    Main client for interacting with the Strava API.
    
    Handles authentication, rate limiting, and provides methods
    for accessing various Strava API endpoints.
    """
    
    BASE_URL = "https://www.strava.com/api/v3"
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Initialize the Strava client.
        
        Args:
            client_id: Strava application client ID
            client_secret: Strava application client secret
        """
        self.client_id = client_id or os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('STRAVA_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID and secret must be provided or set as environment variables")
        
        self.auth = StravaAuth(self.client_id, self.client_secret)
        self.session = requests.Session()
        
    def authenticate(self, code: str = None) -> bool:
        """
        Authenticate with Strava API.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            bool: True if authentication successful
        """
        if code:
            # Exchange code for tokens
            success = self.auth.exchange_code_for_tokens(code)
        else:
            # Start OAuth flow
            success = self.auth.start_oauth_flow()
            
        if success:
            self._setup_session()
            
        return success
    
    def _setup_session(self):
        """Setup the session with authentication headers."""
        token = self.auth.get_access_token()
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated request to the Strava API.
        
        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method
            **kwargs: Additional arguments for requests
            
        Returns:
            dict: API response data
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                # Token might be expired, try to refresh
                if self.auth.refresh_tokens():
                    self._setup_session()
                    # Retry the request
                    response = self.session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            raise
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_athlete(self) -> Dict[str, Any]:
        """
        Get the authenticated athlete's information.
        
        Returns:
            dict: Athlete data
        """
        return self._make_request('/athlete')
    
    def get_activities(self, limit: int = 30, page: int = 1, 
                      before: datetime = None, after: datetime = None) -> List[Dict[str, Any]]:
        """
        Get the authenticated athlete's activities.
        
        Args:
            limit: Number of activities to return (max 200)
            page: Page number for pagination
            before: Return activities before this date
            after: Return activities after this date
            
        Returns:
            list: List of activity data
        """
        params = {
            'per_page': min(limit, 200),
            'page': page
        }
        
        if before:
            params['before'] = int(before.timestamp())
        if after:
            params['after'] = int(after.timestamp())
            
        return self._make_request('/athlete/activities', params=params)
    
    def get_activity(self, activity_id: int, include_efforts: bool = True) -> Dict[str, Any]:
        """
        Get detailed information about a specific activity.
        
        Args:
            activity_id: The activity ID
            include_efforts: Whether to include segment efforts
            
        Returns:
            dict: Detailed activity data
        """
        params = {'include_all_efforts': include_efforts}
        return self._make_request(f'/activities/{activity_id}', params=params)
    
    def get_activity_streams(self, activity_id: int, 
                           types: List[str] = None) -> Dict[str, Any]:
        """
        Get streams for an activity (detailed time-series data).
        
        Args:
            activity_id: The activity ID
            types: List of stream types to fetch (time, distance, altitude, etc.)
            
        Returns:
            dict: Stream data
        """
        if types is None:
            types = ['time', 'distance', 'latlng', 'altitude', 'velocity_smooth', 'heartrate']
            
        stream_types = ','.join(types)
        params = {
            'keys': stream_types,
            'key_by_type': True
        }
        
        return self._make_request(f'/activities/{activity_id}/streams', params=params)
    
    def get_segments(self, activity_id: int) -> List[Dict[str, Any]]:
        """
        Get segments for an activity.
        
        Args:
            activity_id: The activity ID
            
        Returns:
            list: List of segment data
        """
        return self._make_request(f'/activities/{activity_id}/segments')
    
    def get_segment(self, segment_id: int) -> Dict[str, Any]:
        """
        Get information about a specific segment.
        
        Args:
            segment_id: The segment ID
            
        Returns:
            dict: Segment data
        """
        return self._make_request(f'/segments/{segment_id}')
    
    def get_gear(self, gear_id: str) -> Dict[str, Any]:
        """
        Get information about a piece of gear.
        
        Args:
            gear_id: The gear ID
            
        Returns:
            dict: Gear data
        """
        return self._make_request(f'/gear/{gear_id}')
    
    def create_activity(self, name: str, type_: str, start_date: datetime, 
                       elapsed_time: int, **kwargs) -> Dict[str, Any]:
        """
        Create a new activity.
        
        Args:
            name: Activity name
            type_: Activity type (Run, Ride, etc.)
            start_date: Activity start time
            elapsed_time: Activity duration in seconds
            **kwargs: Additional activity parameters
            
        Returns:
            dict: Created activity data
        """
        data = {
            'name': name,
            'type': type_,
            'start_date_local': start_date.isoformat(),
            'elapsed_time': elapsed_time,
            **kwargs
        }
        
        return self._make_request('/activities', method='POST', json=data)
