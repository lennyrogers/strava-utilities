"""
Activity Analysis Module

Provides comprehensive analysis of Strava activity data.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ActivityAnalyzer:
    """
    Analyze Strava activity data to extract insights and statistics.
    """
    
    def __init__(self, activities: List[Dict[str, Any]]):
        """
        Initialize the analyzer with activity data.
        
        Args:
            activities: List of activity dictionaries from Strava API
        """
        self.activities = activities
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from activity data.
        
        Returns:
            pd.DataFrame: Processed activity data
        """
        if not self.activities:
            return pd.DataFrame()
            
        # Extract relevant fields from activities
        data = []
        for activity in self.activities:
            row = {
                'id': activity.get('id'),
                'name': activity.get('name', ''),
                'type': activity.get('type', 'Unknown'),
                'start_date': pd.to_datetime(activity.get('start_date_local')),
                'distance': activity.get('distance', 0) / 1000,  # Convert to km
                'moving_time': activity.get('moving_time', 0) / 60,  # Convert to minutes
                'elapsed_time': activity.get('elapsed_time', 0) / 60,  # Convert to minutes
                'total_elevation_gain': activity.get('total_elevation_gain', 0),
                'average_speed': activity.get('average_speed', 0) * 3.6,  # Convert to km/h
                'max_speed': activity.get('max_speed', 0) * 3.6,  # Convert to km/h
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'suffer_score': activity.get('suffer_score'),
                'kilojoules': activity.get('kilojoules'),
                'achievement_count': activity.get('achievement_count', 0),
                'kudos_count': activity.get('kudos_count', 0),
                'pr_count': activity.get('pr_count', 0)
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Add derived columns
        if not df.empty:
            df['pace'] = df['moving_time'] / df['distance']  # minutes per km
            df['week'] = df['start_date'].dt.isocalendar().week
            df['month'] = df['start_date'].dt.month
            df['year'] = df['start_date'].dt.year
            df['weekday'] = df['start_date'].dt.dayofweek
            df['hour'] = df['start_date'].dt.hour
            
        return df
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of all activities.
        
        Returns:
            dict: Summary statistics
        """
        if self.df.empty:
            return {"message": "No activities to analyze"}
        
        summary = {
            'total_activities': len(self.df),
            'total_distance': self.df['distance'].sum(),
            'total_moving_time': self.df['moving_time'].sum(),
            'total_elevation_gain': self.df['total_elevation_gain'].sum(),
            'average_distance': self.df['distance'].mean(),
            'average_moving_time': self.df['moving_time'].mean(),
            'longest_activity': self.df['distance'].max(),
            'fastest_average_speed': self.df['average_speed'].max(),
            'activity_types': self.df['type'].value_counts().to_dict(),
            'date_range': {
                'start': self.df['start_date'].min().isoformat() if not self.df['start_date'].empty else None,
                'end': self.df['start_date'].max().isoformat() if not self.df['start_date'].empty else None
            },
            'total_kudos': self.df['kudos_count'].sum(),
            'total_achievements': self.df['achievement_count'].sum(),
            'total_prs': self.df['pr_count'].sum()
        }
        
        # Add type-specific summaries
        type_summaries = {}
        for activity_type in self.df['type'].unique():
            type_df = self.df[self.df['type'] == activity_type]
            type_summaries[activity_type] = {
                'count': len(type_df),
                'total_distance': type_df['distance'].sum(),
                'total_time': type_df['moving_time'].sum(),
                'average_speed': type_df['average_speed'].mean(),
                'total_elevation': type_df['total_elevation_gain'].sum()
            }
        
        summary['by_type'] = type_summaries
        
        return summary
    
    def get_weekly_stats(self, weeks: int = 12) -> List[Dict[str, Any]]:
        """
        Get weekly activity statistics.
        
        Args:
            weeks: Number of recent weeks to analyze
            
        Returns:
            list: Weekly statistics
        """
        if self.df.empty:
            return []
        
        # Get recent weeks
        end_date = self.df['start_date'].max()
        start_date = end_date - timedelta(weeks=weeks)
        recent_df = self.df[self.df['start_date'] >= start_date]
        
        weekly_stats = []
        for year_week, group in recent_df.groupby(['year', 'week']):
            year, week = year_week
            stats = {
                'year': year,
                'week': week,
                'activities': len(group),
                'total_distance': group['distance'].sum(),
                'total_time': group['moving_time'].sum(),
                'total_elevation': group['total_elevation_gain'].sum(),
                'avg_speed': group['average_speed'].mean(),
                'by_type': group.groupby('type').agg({
                    'distance': 'sum',
                    'moving_time': 'sum'
                }).to_dict()
            }
            weekly_stats.append(stats)
        
        return sorted(weekly_stats, key=lambda x: (x['year'], x['week']))
    
    def get_monthly_stats(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get monthly activity statistics.
        
        Args:
            months: Number of recent months to analyze
            
        Returns:
            list: Monthly statistics
        """
        if self.df.empty:
            return []
        
        monthly_stats = []
        for year_month, group in self.df.groupby(['year', 'month']):
            year, month = year_month
            stats = {
                'year': year,
                'month': month,
                'activities': len(group),
                'total_distance': group['distance'].sum(),
                'total_time': group['moving_time'].sum(),
                'total_elevation': group['total_elevation_gain'].sum(),
                'avg_speed': group['average_speed'].mean(),
                'by_type': group.groupby('type').agg({
                    'distance': 'sum',
                    'moving_time': 'sum'
                }).to_dict()
            }
            monthly_stats.append(stats)
        
        # Sort and return recent months
        monthly_stats.sort(key=lambda x: (x['year'], x['month']), reverse=True)
        return monthly_stats[:months]
    
    def find_personal_records(self, activity_type: str = None) -> Dict[str, Any]:
        """
        Find personal records in various categories.
        
        Args:
            activity_type: Filter by activity type (optional)
            
        Returns:
            dict: Personal records
        """
        df = self.df
        if activity_type:
            df = df[df['type'] == activity_type]
        
        if df.empty:
            return {}
        
        records = {
            'longest_distance': {
                'value': df['distance'].max(),
                'activity': df.loc[df['distance'].idxmax()]['name'] if not df.empty else None,
                'date': df.loc[df['distance'].idxmax()]['start_date'].isoformat() if not df.empty else None
            },
            'fastest_average_speed': {
                'value': df['average_speed'].max(),
                'activity': df.loc[df['average_speed'].idxmax()]['name'] if not df.empty else None,
                'date': df.loc[df['average_speed'].idxmax()]['start_date'].isoformat() if not df.empty else None
            },
            'most_elevation': {
                'value': df['total_elevation_gain'].max(),
                'activity': df.loc[df['total_elevation_gain'].idxmax()]['name'] if not df.empty else None,
                'date': df.loc[df['total_elevation_gain'].idxmax()]['start_date'].isoformat() if not df.empty else None
            },
            'longest_time': {
                'value': df['moving_time'].max(),
                'activity': df.loc[df['moving_time'].idxmax()]['name'] if not df.empty else None,
                'date': df.loc[df['moving_time'].idxmax()]['start_date'].isoformat() if not df.empty else None
            }
        }
        
        # Add pace record for running activities
        if activity_type == 'Run' or (not activity_type and 'Run' in df['type'].values):
            run_df = df[df['type'] == 'Run'] if not activity_type else df
            if not run_df.empty:
                records['best_pace'] = {
                    'value': run_df['pace'].min(),
                    'activity': run_df.loc[run_df['pace'].idxmin()]['name'],
                    'date': run_df.loc[run_df['pace'].idxmin()]['start_date'].isoformat()
                }
        
        return records
    
    def get_activity_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in activity timing and frequency.
        
        Returns:
            dict: Activity patterns
        """
        if self.df.empty:
            return {}
        
        patterns = {
            'by_day_of_week': self.df.groupby('weekday').size().to_dict(),
            'by_hour_of_day': self.df.groupby('hour').size().to_dict(),
            'by_month': self.df.groupby('month').size().to_dict(),
            'average_activities_per_week': len(self.df) / max(1, self.df['week'].nunique()),
            'most_active_day': self.df['weekday'].mode().iloc[0] if not self.df['weekday'].mode().empty else None,
            'most_active_hour': self.df['hour'].mode().iloc[0] if not self.df['hour'].mode().empty else None,
            'activity_streak': self._calculate_activity_streak()
        }
        
        return patterns
    
    def _calculate_activity_streak(self) -> Dict[str, Any]:
        """
        Calculate current and longest activity streaks.
        
        Returns:
            dict: Streak information
        """
        if self.df.empty:
            return {'current_streak': 0, 'longest_streak': 0}
        
        # Get unique activity dates
        activity_dates = pd.to_datetime(self.df['start_date'].dt.date).unique()
        activity_dates = sorted(activity_dates)
        
        if not activity_dates:
            return {'current_streak': 0, 'longest_streak': 0}
        
        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        # Check if there's an activity today or yesterday
        today = pd.Timestamp.now().normalize()
        yesterday = today - timedelta(days=1)
        
        if activity_dates[-1] == today or activity_dates[-1] == yesterday:
            current_streak = 1
            
            # Count consecutive days backwards
            for i in range(len(activity_dates) - 2, -1, -1):
                expected_date = activity_dates[i + 1] - timedelta(days=1)
                if activity_dates[i] == expected_date:
                    current_streak += 1
                else:
                    break
        
        # Calculate longest streak
        for i in range(1, len(activity_dates)):
            if activity_dates[i] == activity_dates[i-1] + timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }
