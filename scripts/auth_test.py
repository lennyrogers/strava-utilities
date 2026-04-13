#!/usr/bin/env python3
"""
Simple Strava Authentication Test

Test the authentication flow without complex analysis.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path to import strava_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strava_utils import StravaClient


def main():
    """Test Strava authentication."""
    print("🏃 Strava Authentication Test")
    print("=" * 40)
    
    # Check if environment variables are set
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing Strava API credentials!")
        print("\n💡 Setup instructions:")
        print("   1. Copy .env.example to .env")
        print("   2. Get your API credentials from https://www.strava.com/settings/api")
        print("   3. Update .env with your CLIENT_ID and CLIENT_SECRET")
        return
    
    print(f"✅ Found API credentials")
    print(f"   Client ID: {client_id[:10]}...")
    
    try:
        # Initialize client
        client = StravaClient()
        
        # Check authentication status
        if client.auth.is_authenticated():
            print("✅ Already authenticated!")
            
            # Test API call
            try:
                athlete = client.get_athlete()
                print(f"👋 Hello, {athlete.get('firstname', 'Athlete')}!")
                print(f"   Profile: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
                print(f"   Location: {athlete.get('city', 'Unknown')}, {athlete.get('country', 'Unknown')}")
                
                # Get a few recent activities
                print("\n📊 Fetching recent activities...")
                activities = client.get_activities(limit=5)
                print(f"   Found {len(activities)} recent activities")
                
                for i, activity in enumerate(activities[:3], 1):
                    name = activity.get('name', 'Unnamed Activity')
                    distance = activity.get('distance', 0) / 1000  # Convert to km
                    activity_type = activity.get('type', 'Unknown')
                    print(f"   {i}. {name} - {activity_type}, {distance:.2f} km")
                
            except Exception as e:
                print(f"❌ API call failed: {e}")
                
        else:
            print("🔐 Authentication required...")
            print("\n📋 To authenticate:")
            print("   1. The browser will open with Strava's authorization page")
            print("   2. Click 'Authorize' to grant access")
            print("   3. Copy the authorization code from the callback URL")
            print("   4. Paste it when prompted")
            
            # Start OAuth flow
            if client.auth.start_oauth_flow():
                code = input("\n🔑 Enter the authorization code: ").strip()
                if code:
                    if client.auth.exchange_code_for_tokens(code):
                        print("✅ Authentication successful!")
                        print("🎉 You can now use the Strava utilities!")
                        
                        # Test with athlete info
                        try:
                            athlete = client.get_athlete()
                            print(f"👋 Welcome, {athlete.get('firstname', 'Athlete')}!")
                        except Exception as e:
                            print(f"⚠️  Authentication successful but API test failed: {e}")
                    else:
                        print("❌ Authentication failed. Please check the authorization code.")
                else:
                    print("❌ No authorization code provided.")
            else:
                print("❌ Failed to start OAuth flow")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
