import os
import json
import httpx
import base64
import hashlib
import secrets
import re
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from cryptography.fernet import InvalidToken
from urllib.parse import urlencode, parse_qs, urlparse
import sys

from .encryption import decrypt_data, encrypt_data

# Define Project Root and .env path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOTENV_PATH = find_dotenv(str(PROJECT_ROOT / ".env"), usecwd=True, raise_error_if_not_found=False) or PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

class TeslaAuth:
    def __init__(self):
        # Configure client with TLS 1.2 and appropriate timeouts
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            verify=True,
            http2=False,  # Disable HTTP/2 to ensure TLS 1.2
            transport=httpx.AsyncHTTPTransport(
                verify=True,
                retries=3,
                http1=True,  # Force HTTP/1.1
                http2=False  # Disable HTTP/2
            )
        )
        self.auth_domain = "https://auth.tesla.com"
        
        self.access_token = None
        self.refresh_token = None
        self.access_token_expiry = None

    def _generate_code_verifier(self) -> str:
        """Generate a random 86-character alphanumeric string."""
        return secrets.token_urlsafe(64)[:86]

    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate code challenge using SHA-256 and base64url encoding."""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

    def _get_authorization_code_link(self) -> str:
        """Get authorization code url for the oauth3 login method."""
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        state = secrets.token_urlsafe(32)
        query = {
            "client_id": "ownerapi",
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "redirect_uri": "https://auth.tesla.com/void/callback",
            "response_type": "code",
            "scope": "openid email offline_access",
            "state": state,
        }
        return f"{self.auth_domain}/oauth2/v3/authorize?{urlencode(query)}"

    def _prompt_for_manual_auth(self, url: str) -> str:
        """Prompt user to complete authentication in browser and return the code."""
        print("\n=== Tesla Authentication Required ===", file=sys.stderr)
        print("1. Open this URL in your browser:", file=sys.stderr)
        print(f"   {url}", file=sys.stderr)
        print("2. Log in and complete any 2FA", file=sys.stderr)
        print("3. You'll see 'Page Not Found' - this is expected", file=sys.stderr)
        print("4. Copy the URL from your browser's address bar", file=sys.stderr)
        print("5. Paste it below and press Enter", file=sys.stderr)
        print("=========================================\n", file=sys.stderr)
        
        while True:
            callback_url = input("Paste the callback URL: ").strip()
            if 'code=' in callback_url:
                code = parse_qs(urlparse(callback_url).query)["code"][0]
                return code
            print("Invalid URL. Make sure it contains 'code=' parameter.", file=sys.stderr)

    def _save_refresh_token(self, refresh_token: str) -> None:
        """Save refresh token."""
        token_file = PROJECT_ROOT / "refresh_token.txt"
        with open(token_file, "w") as f:
            f.write(refresh_token)

    def _load_refresh_token(self) -> Optional[str]:
        """Load refresh token."""
        token_file = PROJECT_ROOT / "refresh_token.txt"
        if not token_file.exists():
            return None
        try:
            with open(token_file, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not load refresh token: {e}", file=sys.stderr)
            return None

    def has_valid_refresh_token(self) -> bool:
        """Check if we have a valid refresh token."""
        self.refresh_token = self._load_refresh_token()
        return bool(self.refresh_token)

    async def _exchange_code_for_tokens(self, code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens."""
        token_url = f"{self.auth_domain}/oauth2/v3/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": "ownerapi",
            "code": code,
            "code_verifier": self.code_verifier,
            "redirect_uri": "https://auth.tesla.com/void/callback"
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "python-httpx/0.24.1"
        }
        
        print(f"[DEBUG] Token request URL: {token_url}", file=sys.stderr)
        print(f"[DEBUG] Token request data: {json.dumps(data, indent=2)}", file=sys.stderr)
        
        response = await self.client.post(token_url, json=data, headers=headers)
        print(f"[DEBUG] Token response status: {response.status_code}", file=sys.stderr)
        print(f"[DEBUG] Token response body: {response.text}", file=sys.stderr)
        
        response.raise_for_status()
        token_data = response.json()
        
        # No longer need the Owner API exchange - use auth.tesla.com token directly
        return token_data

    async def authenticate_once(self) -> str:
        """One-time authentication that saves refresh token."""
        if self.has_valid_refresh_token():
            return await self.refresh_access_token()
        
        # Manual browser flow
        url = self._get_authorization_code_link()
        code = self._prompt_for_manual_auth(url)
        
        # Get tokens
        token_data = await self._exchange_code_for_tokens(code)
        
        # Save refresh token securely for future use
        self._save_refresh_token(token_data['refresh_token'])
        
        # Update instance variables
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.access_token_expiry = datetime.now() + timedelta(hours=8)
        
        return self.access_token

    async def refresh_access_token(self) -> str:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            return await self.authenticate_once()
            
        token_url = f"{self.auth_domain}/oauth2/v3/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": "ownerapi",
            "refresh_token": self.refresh_token,
            "scope": "openid email offline_access"
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "python-httpx/0.24.1"
        }
        
        try:
            response = await self.client.post(token_url, json=data, headers=headers)
            response.raise_for_status()
            token_data = response.json()
            
            # Use the auth.tesla.com token directly
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)
            self.access_token_expiry = datetime.now() + timedelta(hours=8)
            
            # Save new refresh token if provided
            if "refresh_token" in token_data:
                self._save_refresh_token(token_data["refresh_token"])
                
            return self.access_token
            
        except Exception as e:
            print(f"[ERROR] Failed to refresh token: {str(e)}", file=sys.stderr)
            if hasattr(e, 'response'):
                print(f"[ERROR] Response status: {e.response.status_code}", file=sys.stderr)
                print(f"[ERROR] Response body: {e.response.text}", file=sys.stderr)
            # If refresh fails, do a full re-authentication
            return await self.authenticate_once()

    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self.access_token and self.access_token_expiry and datetime.now() < self.access_token_expiry:
            return self.access_token
        return await self.refresh_access_token()

    async def get_vehicles(self):
        """Get vehicles using fallback endpoints."""
        headers = {
            "Authorization": f"Bearer {await self.get_valid_token()}",
            "User-Agent": "python-httpx/0.24.1"
        }
        
        try:
            # Try vehicles endpoint first
            response = await self.client.get(
                "https://owner-api.teslamotors.com/api/1/vehicles",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[DEBUG] Vehicles endpoint returned {response.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] Vehicles endpoint failed: {str(e)}", file=sys.stderr)
        
        # Fallback to products endpoint
        try:
            print("[DEBUG] Trying products endpoint...", file=sys.stderr)
            response = await self.client.get(
                "https://owner-api.teslamotors.com/api/1/products",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            print(f"[DEBUG] Products response: {data}", file=sys.stderr)
            
            # Filter for vehicles only
            vehicles = [p for p in data['response'] if 'vin' in p]
            print(f"[DEBUG] Found {len(vehicles)} vehicles", file=sys.stderr)
            return {"response": vehicles}
        except Exception as e:
            print(f"[ERROR] Products endpoint also failed: {str(e)}", file=sys.stderr)
            raise 