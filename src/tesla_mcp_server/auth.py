import os
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
from python_dotenv import load_dotenv, find_dotenv
from cryptography.fernet import InvalidToken
from urllib.parse import urlencode

from .encryption import decrypt_data

# Define Project Root and .env path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = find_dotenv(str(PROJECT_ROOT / ".env"), usecwd=True, raise_error_if_not_found=False) or PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)
# print(f"Loading environment variables from: {DOTENV_PATH}") # Optional: for debugging .env loading

class TeslaAuth:
    def __init__(self):
        # Load Encryption Key
        encryption_key_str = os.getenv("ENCRYPTION_KEY")
        if not encryption_key_str:
            raise ValueError("ENCRYPTION_KEY not found. Please run scripts/encrypt_creds.py or set it in your .env file.")
        encryption_key_bytes = encryption_key_str.encode('utf-8')

        # Load and Decrypt Credentials
        credentials_file = PROJECT_ROOT / "credentials.enc"
        if not credentials_file.exists():
            raise FileNotFoundError(f"Encrypted credentials file not found at {credentials_file}. Please run scripts/encrypt_creds.py.")

        with open(credentials_file, "rb") as f:
            encrypted_creds = f.read()

        try:
            decrypted_creds_bytes = decrypt_data(encrypted_creds, encryption_key_bytes)
        except InvalidToken:
            raise ValueError("Failed to decrypt credentials. Ensure ENCRYPTION_KEY is correct and credentials.enc is valid.")
        
        credentials = json.loads(decrypted_creds_bytes.decode('utf-8'))
        
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        
        self.access_token = None
        self.access_token_expiry = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID or Client Secret not found in decrypted credentials.")

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