"""
Strava OAuth2 Authentication

Handles OAuth2 flow for Strava API authentication.
"""

import os
import webbrowser
import json
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class StravaAuth:
    """
    Handles OAuth2 authentication flow for Strava API.
    
    Manages access tokens, refresh tokens, and handles token refresh.
    """
    
    AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = None):
        """
        Initialize the authentication handler.
        
        Args:
            client_id: Strava application client ID
            client_secret: Strava application client secret
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or os.getenv('STRAVA_REDIRECT_URI', 'http://localhost:8080/auth/callback')
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # Try to load existing tokens
        self._load_tokens()
    
    def start_oauth_flow(self) -> bool:
        """
        Start the OAuth2 flow by opening the browser.
        
        Returns:
            bool: True if flow started successfully
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'read,activity:read_all,profile:read_all',
            'state': 'auth'
        }
        
        auth_url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"
        
        print(f"Opening browser for Strava authentication...")
        print(f"If browser doesn't open, visit: {auth_url}")
        
        try:
            webbrowser.open(auth_url)
            
            # In a real implementation, you'd set up a local server to catch the callback
            print("\nAfter authorizing, you'll be redirected to a URL.")
            print("Copy the 'code' parameter from that URL and use it to complete authentication.")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            return False
    
    def exchange_code_for_tokens(self, code: str) -> bool:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            bool: True if tokens obtained successfully
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.token_expires_at = datetime.fromtimestamp(token_data['expires_at'])
            
            # Save tokens for future use
            self._save_tokens()
            
            logger.info("Successfully obtained access tokens")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return False
        except KeyError as e:
            logger.error(f"Unexpected token response format: {e}")
            return False
    
    def refresh_tokens(self) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            bool: True if tokens refreshed successfully
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
            
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.token_expires_at = datetime.fromtimestamp(token_data['expires_at'])
            
            # Save updated tokens
            self._save_tokens()
            
            logger.info("Successfully refreshed access tokens")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh tokens: {e}")
            return False
        except KeyError as e:
            logger.error(f"Unexpected token response format: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token or None if unavailable
        """
        if not self.access_token:
            return None
            
        # Check if token is expired (with 5 minute buffer)
        if self.token_expires_at and datetime.now() > (self.token_expires_at - timedelta(minutes=5)):
            if not self.refresh_tokens():
                return None
                
        return self.access_token
    
    def is_authenticated(self) -> bool:
        """
        Check if we have valid authentication.
        
        Returns:
            bool: True if authenticated
        """
        return self.get_access_token() is not None
    
    def _save_tokens(self):
        """Save tokens to a local file."""
        token_data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.token_expires_at.timestamp() if self.token_expires_at else None
        }
        
        try:
            with open('.strava_tokens.json', 'w') as f:
                json.dump(token_data, f)
            logger.debug("Tokens saved to .strava_tokens.json")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
    
    def _load_tokens(self):
        """Load tokens from a local file."""
        try:
            with open('.strava_tokens.json', 'r') as f:
                token_data = json.load(f)
                
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            if token_data.get('expires_at'):
                self.token_expires_at = datetime.fromtimestamp(token_data['expires_at'])
                
            logger.debug("Tokens loaded from .strava_tokens.json")
            
        except FileNotFoundError:
            logger.debug("No existing token file found")
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
    
    def revoke_tokens(self):
        """Revoke and clear all tokens."""
        if self.access_token:
            try:
                # Strava doesn't have a revoke endpoint, so we just clear locally
                self.access_token = None
                self.refresh_token = None
                self.token_expires_at = None
                
                # Remove token file
                if os.path.exists('.strava_tokens.json'):
                    os.remove('.strava_tokens.json')
                    
                logger.info("Tokens revoked and cleared")
                
            except Exception as e:
                logger.error(f"Failed to revoke tokens: {e}")
