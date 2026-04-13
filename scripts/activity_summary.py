#!/usr/bin/env python3
"""
Activity Summary Script

Generate a comprehensive summary of your Strava activities.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import strava_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strava_utils import StravaClient
from strava_utils.analysis import ActivityAnalyzer


def main():
    """Generate and display activity summary."""
    print("🏃 Strava Activity Summary Generator")
    print("=" * 50)
    
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
    
    print("📊 Fetching activity data...")
    
    try:
        # Get recent activities (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        activities = client.get_activities(limit=200, after=six_months_ago)
        
        print(f"📈 Found {len(activities)} activities")
        
        if not activities:
            print("❌ No activities found. Make sure you have activities on Strava!")
            return
        
        # Analyze activities
        analyzer = ActivityAnalyzer(activities)
        summary = analyzer.generate_summary()
        
        # Display summary
        print("\n" + "=" * 50)
        print("📋 ACTIVITY SUMMARY")
        print("=" * 50)
        
        print(f"Total Activities: {summary['total_activities']}")
        print(f"Total Distance: {summary['total_distance']:.2f} km")
        print(f"Total Moving Time: {summary['total_moving_time']:.1f} minutes ({summary['total_moving_time']/60:.1f} hours)")
        print(f"Total Elevation Gain: {summary['total_elevation_gain']:.0f} m")
        print(f"Average Distance: {summary['average_distance']:.2f} km")
        print(f"Longest Activity: {summary['longest_activity']:.2f} km")
        print(f"Fastest Average Speed: {summary['fastest_average_speed']:.2f} km/h")
        
        # Activity types
        print(f"\n📊 ACTIVITY TYPES:")
        for activity_type, count in summary['activity_types'].items():
            print(f"   {activity_type}: {count} activities")
        
        # Type-specific summaries
        print(f"\n🎯 BY ACTIVITY TYPE:")
        for activity_type, stats in summary['by_type'].items():
            print(f"   {activity_type}:")
            print(f"      Distance: {stats['total_distance']:.2f} km")
            print(f"      Time: {stats['total_time']:.1f} minutes")
            print(f"      Avg Speed: {stats['average_speed']:.2f} km/h")
            print(f"      Elevation: {stats['total_elevation']:.0f} m")
        
        # Date range
        if summary['date_range']['start'] and summary['date_range']['end']:
            start_date = datetime.fromisoformat(summary['date_range']['start']).strftime('%Y-%m-%d')
            end_date = datetime.fromisoformat(summary['date_range']['end']).strftime('%Y-%m-%d')
            print(f"\n📅 DATE RANGE: {start_date} to {end_date}")
        
        # Social stats
        print(f"\n👍 SOCIAL STATS:")
        print(f"   Total Kudos: {summary['total_kudos']}")
        print(f"   Total Achievements: {summary['total_achievements']}")
        print(f"   Total PRs: {summary['total_prs']}")
        
        # Weekly stats
        weekly_stats = analyzer.get_weekly_stats(weeks=4)
        if weekly_stats:
            print(f"\n📈 RECENT WEEKLY STATS:")
            for week in weekly_stats[-4:]:  # Last 4 weeks
                print(f"   Week {week['week']}/{week['year']}: {week['activities']} activities, {week['total_distance']:.1f} km")
        
        # Personal records
        print(f"\n🏆 PERSONAL RECORDS (All Types):")
        records = analyzer.find_personal_records()
        for record_type, record_data in records.items():
            if record_data and record_data.get('value'):
                value = record_data['value']
                activity_name = record_data.get('activity', 'Unknown')
                date = record_data.get('date', 'Unknown')
                
                if record_type == 'longest_distance':
                    print(f"   Longest Distance: {value:.2f} km ({activity_name})")
                elif record_type == 'fastest_average_speed':
                    print(f"   Fastest Avg Speed: {value:.2f} km/h ({activity_name})")
                elif record_type == 'most_elevation':
                    print(f"   Most Elevation: {value:.0f} m ({activity_name})")
                elif record_type == 'longest_time':
                    print(f"   Longest Time: {value:.1f} minutes ({activity_name})")
                elif record_type == 'best_pace':
                    print(f"   Best Pace: {value:.2f} min/km ({activity_name})")
        
        # Activity patterns
        patterns = analyzer.get_activity_patterns()
        if patterns:
            print(f"\n📊 ACTIVITY PATTERNS:")
            print(f"   Average activities per week: {patterns.get('average_activities_per_week', 0):.1f}")
            
            if patterns.get('activity_streak'):
                streak = patterns['activity_streak']
                print(f"   Current streak: {streak['current_streak']} days")
                print(f"   Longest streak: {streak['longest_streak']} days")
        
        print("\n✅ Summary complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
