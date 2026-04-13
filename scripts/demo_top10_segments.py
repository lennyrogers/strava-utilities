#!/usr/bin/env python3
"""
Quick demo of the Top 10 Segments Finder

This is a simplified version to test the functionality with fewer activities.
"""

import os
import sys

# Add the parent directory to sys.path to import strava_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strava_utils import StravaClient
from scripts.find_top10_segments import Top10SegmentFinder


def quick_demo():
    """Quick demo with just a few activities."""
    print("🚀 Quick Top 10 Segments Demo")
    print("=" * 40)
    
    try:
        # Initialize client
        client = StravaClient()
        
        # Check if authenticated
        if not client.auth.is_authenticated():
            print("❌ Not authenticated. Please run the main script first to authenticate.")
            return
        
        # Initialize finder
        finder = Top10SegmentFinder(client)
        
        # Get athlete info
        athlete = finder.get_athlete_info()
        if not athlete:
            print("❌ Could not get athlete information")
            return
            
        print(f"👋 Hello, {athlete.get('firstname', 'Athlete')}!")
        
        # Quick search with just 10 activities from last 30 days
        print("\n🔍 Quick search: 10 recent activities, last 30 days")
        segments = finder.find_top_10_segments(activity_limit=10, days_back=30)
        
        # Display results
        finder.display_results()
        
        if segments:
            print(f"\n✅ Found {len(segments)} potential segments!")
            print("💡 Run the full script for a comprehensive analysis")
        else:
            print("\n📊 No top 10 segments found in recent activities")
            print("💡 Try the full script with more activities and a longer time range")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you've set up authentication first")


if __name__ == "__main__":
    quick_demo()
