# Top 10 Segments Finder

Find all Strava segments where you're in the top 10 but not the King/Queen of the Mountain (KOM/QOM). This helps identify segments where you have a good chance of improving your ranking or achieving a personal record.

## What it does

The script analyzes your recent Strava activities and:
1. Finds all segments from your activities
2. Checks your ranking on each segment's leaderboard
3. Identifies segments where you rank 2-10 (top 10 but not KOM)
4. Shows how close you are to the KOM time
5. Provides detailed segment information for targeted training

## Files

- `find_top10_segments.py` - Main comprehensive analysis script
- `demo_top10_segments.py` - Quick demo with limited scope
- `top10_segments_README.md` - This documentation

## Setup

1. **Authentication**: Make sure you've completed Strava authentication first:
   ```bash
   python scripts/auth_test.py
   ```

2. **Run the demo** (quick test with 10 activities):
   ```bash
   python scripts/demo_top10_segments.py
   ```

3. **Run full analysis** (comprehensive search):
   ```bash
   python scripts/find_top10_segments.py
   ```

## Usage Options

### Quick Demo
```bash
python scripts/demo_top10_segments.py
```
- Analyzes 10 recent activities
- Looks back 30 days
- Fast execution for testing

### Full Analysis
```bash
python scripts/find_top10_segments.py
```
Interactive prompts for:
- Number of activities to analyze (default: 50)
- Days to look back (default: 180)
- Option to save results to JSON file

## Sample Output

```
🏆 Found 5 segments where you're in the top 10 but not KOM!
================================================================================

1. Hawk Hill Climb
   📍 Rank: #3 / Top 10
   ⏱️  Your Time: 4:23
   👑 KOM Time: 4:01
   🎯 Time Behind KOM: 22.0 seconds
   📏 Distance: 1.2 km
   🏃 From Activity: Morning Ride to Marin
   📅 Date: 2026-03-15
   🔗 Segment ID: 12345678

2. Golden Gate Park Loop
   📍 Rank: #7 / Top 10
   ⏱️  Your Time: 12:45
   👑 KOM Time: 11:30
   🎯 Time Behind KOM: 75.0 seconds
   📏 Distance: 3.8 km
   🏃 From Activity: Weekend Coffee Ride
   📅 Date: 2026-03-10
   🔗 Segment ID: 87654321
```

## Features

### Smart Analysis
- **Rate Limiting**: Respects Strava API limits with automatic delays
- **Duplicate Prevention**: Only analyzes each segment once
- **Error Handling**: Gracefully handles private segments and API errors

### Detailed Information
- Your current ranking (2-10 only)
- Time difference to KOM
- Segment distance and difficulty
- Source activity information
- Direct links to segments

### Export Options
- Save results to JSON file
- Timestamp-based filenames
- All data preserved for further analysis

## Pro Tips

### Target Selection
- **Close to KOM**: Focus on segments where you're within 30 seconds of KOM
- **Recent Activities**: Check if you were having a good/bad day
- **Segment Accuracy**: Verify the segment is still active and accurate

### Strategy
- **Weather Conditions**: Plan attempts for optimal weather
- **Traffic**: Consider time of day for urban segments  
- **Training**: Use data to identify specific weaknesses
- **Equipment**: Consider if gear changes could help

### Rate Limiting
The script includes built-in protections:
- 0.5 second delay between activities
- 15 second wait when rate limits are hit
- Automatic retry logic for authentication

## Troubleshooting

### Common Issues

1. **"Not authenticated"**
   ```bash
   # Run authentication first
   python scripts/auth_test.py
   ```

2. **"No segments found"**
   - Increase activity limit (try 100+)
   - Extend date range (try 365 days)
   - Check if you've ridden segments recently

3. **Rate limiting errors**
   - Script handles this automatically
   - Be patient with large analyses
   - Consider smaller batches for very large datasets

4. **Private segments**
   - These are automatically skipped
   - No ranking data available for private segments

### Performance Tips

- Start with demo script to verify setup
- Use smaller activity counts for testing
- Full analysis can take 10-30 minutes for 100+ activities
- Save results to avoid re-running large analyses

## Data Structure

### Saved JSON Format
```json
{
  "segment_id": 12345678,
  "segment_name": "Hawk Hill Climb",
  "rank": 3,
  "time": 263,
  "kom_time": 241,
  "time_behind_kom": 22.0,
  "segment_distance": 1200.5,
  "activity_name": "Morning Ride to Marin",
  "activity_date": "2026-03-15T08:30:00Z",
  "effort_id": 98765432
}
```

## API Rate Limits

Strava API limits:
- 100 requests per 15 minutes
- 1,000 requests per day

The script manages these automatically but large analyses may take time.

## Next Steps

After finding your top 10 segments:
1. **Plan Training**: Focus on weaknesses revealed by segment analysis
2. **Schedule Attempts**: Pick optimal conditions for PR attempts  
3. **Track Progress**: Re-run analysis to see improvements
4. **Share Results**: Use segment IDs to share with training partners
5. **Analyze Patterns**: Look for common segment types where you excel

Happy segment hunting! 🏆
