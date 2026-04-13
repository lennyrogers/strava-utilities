"""
Strava Utilities Package

A comprehensive toolkit for working with Strava API and activity data.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import StravaClient
from .auth import StravaAuth

__all__ = ["StravaClient", "StravaAuth"]
