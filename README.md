# Strava Utilities

A comprehensive Python toolkit for working with Strava API, analyzing activity data, and building utilities for athletes and coaches.

## Features

- 🏃‍♂️ **Strava API Integration** - Complete OAuth2 authentication and API client
- 📊 **Activity Analysis** - Detailed analysis of running, cycling, and other activities
- 📈 **Data Visualization** - Charts and graphs for performance tracking
- 🛠️ **Utility Scripts** - Common tasks and data processing tools
- 📋 **Reporting** - Generate comprehensive activity reports
- 🔄 **Data Export/Import** - Backup and sync your Strava data

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Strava Developer Account (for API access)
- pip package manager

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/strava-utilities.git
   cd strava-utilities
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your Strava API credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your Strava API credentials
   ```

### Basic Usage

```python
from strava_utils import StravaClient

# Initialize client
client = StravaClient()

# Authenticate (opens browser for OAuth)
client.authenticate()

# Get recent activities
activities = client.get_activities(limit=10)

# Analyze activity data
from strava_utils.analysis import ActivityAnalyzer
analyzer = ActivityAnalyzer(activities)
summary = analyzer.generate_summary()
print(summary)
```

## Project Structure

```
strava-utilities/
├── strava_utils/          # Main package
│   ├── __init__.py
│   ├── client.py          # Strava API client
│   ├── auth.py           # Authentication handling
│   ├── analysis/         # Data analysis modules
│   ├── visualization/    # Charts and graphs
│   └── utils/           # Utility functions
├── scripts/              # Utility scripts
├── examples/            # Example usage
├── tests/              # Unit tests
├── docs/               # Documentation
├── .env.example        # Environment template
├── requirements.txt    # Dependencies
└── setup.py           # Package setup
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REDIRECT_URI=http://localhost:8080/auth/callback
```

## Available Utilities

- **Activity Downloader** - Bulk download activity data
- **Performance Tracker** - Track PRs and improvements
- **Route Analyzer** - Analyze popular routes and segments
- **Training Load Calculator** - Calculate training stress and load
- **Gear Usage Tracker** - Monitor equipment usage and maintenance

## Development

### Setting up for Development

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Format code
black strava_utils/
flake8 strava_utils/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## API Reference

### StravaClient

Main client for interacting with Strava API.

```python
client = StravaClient(client_id, client_secret)
client.authenticate()
activities = client.get_activities()
```

### ActivityAnalyzer

Analyze activity data and generate insights.

```python
analyzer = ActivityAnalyzer(activities)
stats = analyzer.calculate_weekly_stats()
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is not affiliated with Strava. Use in accordance with Strava's API Terms of Service.
