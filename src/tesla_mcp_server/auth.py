import os
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv
from urllib.parse import urlencode

# Load environment variables from .env file in project root
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading environment variables from: {env_path}")
load_dotenv(env_path)

class TeslaAuth:
    def __init__(self):
        self.client_id = os.getenv("TESLA_CLIENT_ID")
        self.client_secret = os.getenv("TESLA_CLIENT_SECRET")
        self.access_token = None
        self.access_token_expiry = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("TESLA_CLIENT_ID and TESLA_CLIENT_SECRET must be set in .env file")
        
        # Debug logging for environment variables
        print(f"Client ID loaded: {self.client_id}")
        print(f"Client Secret loaded: {self.client_secret[:5]}...{self.client_secret[-4:]}")

    async def get_access_token(self):
        """Get an access token using client credentials"""
        if self.access_token and self.access_token_expiry and datetime.now() < self.access_token_expiry:
            return self.access_token

        print("Getting access token...")
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "vehicle_device_data vehicle_commands vehicle_telemetry energy_device_data",
            "audience": "https://fleet-api.prd.na.vn.cloud.tesla.com"
        }

        print(f"Request data: {data}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://auth.tesla.com/oauth2/v3/token",
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "TeslaMCP/1.0",
                        "Accept": "application/json"
                    }
                )
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response body: {response.text}")

                response.raise_for_status()
                token_data = response.json()
                
                self.access_token = token_data["access_token"]
                self.access_token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
                
                return self.access_token
            except Exception as e:
                print(f"Error getting access token: {str(e)}")
                if hasattr(e, "response"):
                    error_detail = e.response.json()
                    print(f"Error response: {error_detail}")
                    raise Exception(f"Failed to get access token: {error_detail}")
                raise

    async def get_valid_token(self):
        """Get a valid token, refreshing if necessary"""
        if self.access_token and self.access_token_expiry and datetime.now() < self.access_token_expiry:
            return self.access_token
        return await self.get_access_token() 