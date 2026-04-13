#!/usr/bin/env python3
"""
Top 10 Segments Finder

Find all Strava segments where you're in the top 10 but not the KOM.
This helps identify segments where you have a good chance of improving your ranking.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path to import strava_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strava_utils import StravaClient


class Top10SegmentFinder:
    """Find segments where athlete is in top 10 but not KOM."""
    
    def __init__(self, client: StravaClient):
        self.client = client
        self.athlete_id = None
        self.top_10_segments = []
        
    def get_athlete_info(self) -> Dict[str, Any]:
        """Get authenticated athlete information."""
        try:
            athlete = self.client.get_athlete()
            self.athlete_id = athlete['id']
            return athlete
        except Exception as e:
            print(f"❌ Error getting athlete info: {e}")
            return None
    
    def find_top_10_segments(self, activity_limit: int = 100, days_back: int = 365) -> List[Dict[str, Any]]:
        """
        Find segments where athlete is in top 10 but not KOM.
        
        Args:
            activity_limit: Number of recent activities to check
            days_back: How many days back to look for activities
            
        Returns:
            List of segment data with ranking information
        """
        if not self.athlete_id:
            print("❌ Athlete ID not available. Please authenticate first.")
            return []
        
        print(f"🔍 Searching through last {activity_limit} activities from past {days_back} days...")
        
        # Get recent activities
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            activities = self.client.get_activities(limit=activity_limit, after=cutoff_date)
            print(f"📊 Found {len(activities)} activities to analyze")
        except Exception as e:
            print(f"❌ Error fetching activities: {e}")
            return []
        
        segment_efforts = {}
        processed_activities = 0
        
        for activity in activities:
            processed_activities += 1
            activity_id = activity['id']
            activity_name = activity['name']
            activity_date = activity['start_date_local']
            
            print(f"🏃 Analyzing activity {processed_activities}/{len(activities)}: {activity_name[:50]}...")
            
            try:
                # Get detailed activity with segment efforts
                detailed_activity = self.client.get_activity(activity_id, include_efforts=True)
                
                if 'segment_efforts' not in detailed_activity:
                    continue
                
                # Process each segment effort
                for effort in detailed_activity['segment_efforts']:
                    segment_id = effort['segment']['id']
                    segment_name = effort['segment']['name']
                    
                    # Skip if we've already processed this segment
                    if segment_id in segment_efforts:
                        continue
                    
                    # Get segment leaderboard to check ranking
                    try:
                        leaderboard_info = self._get_segment_ranking(segment_id, effort)
                        if leaderboard_info and leaderboard_info['rank'] <= 10 and leaderboard_info['rank'] > 1:
                            segment_data = {
                                'segment_id': segment_id,
                                'segment_name': segment_name,
                                'rank': leaderboard_info['rank'],
                                'time': leaderboard_info['time'],
                                'kom_time': leaderboard_info['kom_time'],
                                'time_behind_kom': leaderboard_info['time_behind_kom'],
                                'segment_distance': effort['segment']['distance'],
                                'activity_name': activity_name,
                                'activity_date': activity_date,
                                'effort_id': effort['id']
                            }
                            
                            segment_efforts[segment_id] = segment_data
                            self.top_10_segments.append(segment_data)
                            
                            print(f"   🎯 Found top 10 segment: {segment_name} (Rank #{leaderboard_info['rank']})")
                    
                    except Exception as e:
                        # Rate limiting or API error - add small delay
                        if "rate limit" in str(e).lower():
                            print(f"   ⏳ Rate limit hit, waiting...")
                            time.sleep(15)  # Wait 15 seconds for rate limit
                        continue
                
                # Small delay between activities to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error processing activity {activity_name}: {e}")
                continue
        
        return self.top_10_segments
    
    def _get_segment_ranking(self, segment_id: int, effort: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the athlete's ranking on a segment.
        
        Args:
            segment_id: The segment ID
            effort: The segment effort data
            
        Returns:
            Dict with ranking information or None if not in top 10
        """
        try:
            # Get leaderboard (top 10)
            leaderboard = self.client.get_segment_leaderboard(segment_id, per_page=10, page=1)
            
            if 'entries' not in leaderboard:
                return None
            
            # Find athlete's ranking
            athlete_rank = None
            kom_time = None
            athlete_time = effort.get('elapsed_time')  # Use effort time from activity
            
            for i, entry in enumerate(leaderboard['entries']):
                rank = i + 1
                
                # KOM time (first place)
                if rank == 1:
                    kom_time = entry['elapsed_time']
                
                # Check if this is our athlete
                if entry['athlete_id'] == self.athlete_id:
                    athlete_rank = rank
                    athlete_time = entry['elapsed_time']
                    break
            
            if athlete_rank and athlete_rank <= 10 and athlete_rank > 1:
                time_behind_kom = athlete_time - kom_time if athlete_time and kom_time else None
                
                return {
                    'rank': athlete_rank,
                    'time': athlete_time,
                    'kom_time': kom_time,
                    'time_behind_kom': time_behind_kom
                }
            
            return None
            
        except Exception as e:
            # Likely a private segment or API error
            return None
    
    def display_results(self):
        """Display the top 10 segments in a formatted way."""
        if not self.top_10_segments:
            print("\n📊 No segments found where you're in the top 10 but not KOM.")
            print("💡 This could mean:")
            print("   - You're already KOM on most segments you've ridden")
            print("   - You haven't ridden many segments recently")
            print("   - Try increasing the activity_limit or days_back parameters")
            return
        
        # Sort by rank (best rank first)
        sorted_segments = sorted(self.top_10_segments, key=lambda x: x['rank'])
        
        print(f"\n🏆 Found {len(sorted_segments)} segments where you're in the top 10 but not KOM!")
        print("=" * 80)
        
        for i, segment in enumerate(sorted_segments, 1):
            print(f"\n{i}. {segment['segment_name']}")
            print(f"   📍 Rank: #{segment['rank']} / Top 10")
            print(f"   ⏱️  Your Time: {self._format_time(segment['time'])}")
            print(f"   👑 KOM Time: {self._format_time(segment['kom_time'])}")
            
            if segment['time_behind_kom']:
                print(f"   🎯 Time Behind KOM: {segment['time_behind_kom']:.1f} seconds")
            
            distance_km = segment['segment_distance'] / 1000
            print(f"   📏 Distance: {distance_km:.2f} km")
            print(f"   🏃 From Activity: {segment['activity_name']}")
            print(f"   📅 Date: {segment['activity_date'][:10]}")
            print(f"   🔗 Segment ID: {segment['segment_id']}")
    
    def save_results(self, filename: str = None):
        """Save results to a JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"top_10_segments_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.top_10_segments, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds into MM:SS format."""
        if not seconds:
            return "Unknown"
        
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


def main():
    """Main function to find top 10 segments."""
    print("🏆 Strava Top 10 Segments Finder")
    print("=" * 50)
    print("Find segments where you're in the top 10 but not the KOM!")
    
    # Initialize client
    try:
        client = StravaClient()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure to:")
        print("   1. Copy .env.example to .env")
        print("   2. Fill in your Strava API credentials")
        return
    
    # Check authentication
    if not client.auth.is_authenticated():
        print("🔐 Authentication required...")
        print("\n1. Visit https://www.strava.com/settings/api to get your credentials")
        print("2. Update your .env file with CLIENT_ID and CLIENT_SECRET")
        print("3. Run the authentication flow:")
        
        # Start OAuth flow
        if client.auth.start_oauth_flow():
            code = input("\nEnter the authorization code from the callback URL: ")
            if client.auth.exchange_code_for_tokens(code):
                print("✅ Authentication successful!")
            else:
                print("❌ Authentication failed")
                return
        else:
            print("❌ Failed to start OAuth flow")
            return
    
    # Initialize finder
    finder = Top10SegmentFinder(client)
    
    # Get athlete info
    athlete = finder.get_athlete_info()
    if not athlete:
        return
    
    print(f"👋 Hello, {athlete.get('firstname', 'Athlete')}!")
    print(f"🔍 Searching for segments where you're in the top 10...")
    
    # Get user preferences
    try:
        activity_limit = input("\nHow many recent activities to check? (default: 50): ")
        activity_limit = int(activity_limit) if activity_limit else 50
        
        days_back = input("How many days back to look? (default: 180): ")
        days_back = int(days_back) if days_back else 180
        
    except ValueError:
        activity_limit = 50
        days_back = 180
    
    print(f"\n🚀 Starting analysis...")
    print(f"   📊 Activities: {activity_limit}")
    print(f"   📅 Days back: {days_back}")
    print(f"   ⚠️  Note: This may take a while due to API rate limits")
    
    # Find segments
    segments = finder.find_top_10_segments(activity_limit=activity_limit, days_back=days_back)
    
    # Display results
    finder.display_results()
    
    # Save results
    if segments:
        save = input("\n💾 Save results to file? (y/n): ").lower().strip()
        if save in ['y', 'yes']:
            finder.save_results()
    
    print("\n✅ Analysis complete!")
    print("\n💡 Pro Tips:")
    print("   - Focus on segments where you're close to KOM time")
    print("   - Consider weather and traffic conditions for your attempts")
    print("   - Check if the segment is still active and accurate")


if __name__ == "__main__":
    main()
