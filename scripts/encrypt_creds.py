#!/usr/bin/env python3

import os
import json
import getpass
from pathlib import Path
import sys

# Path Setup
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
# Add src directory to sys.path to allow importing tesla_mcp_server components
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv, find_dotenv
from tesla_mcp_server.encryption import generate_key, encrypt_data

# Define paths for credentials and .env file
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.enc"
# Try to find .env, default to project root if not found by find_dotenv
# usecwd=True ensures find_dotenv looks in the current working directory if PROJECT_ROOT/.env is not found
# This handles cases where the script might be run from a different directory
DOTENV_PATH = find_dotenv(filename=str(PROJECT_ROOT / ".env"), usecwd=True, raise_error_if_not_found=False) or PROJECT_ROOT / ".env"

def main():
    # Load Environment Variables
    load_dotenv(dotenv_path=DOTENV_PATH)
    encryption_key_str = os.getenv("ENCRYPTION_KEY")

    # Encryption Key Handling
    if not encryption_key_str:
        print("ENCRYPTION_KEY not found in your .env file or environment. A new key will be generated.")
        new_key_bytes = generate_key()
        new_key_str = new_key_bytes.decode('utf-8')
        
        try:
            env_content = ""
            if os.path.exists(DOTENV_PATH):
                with open(DOTENV_PATH, 'r') as f_read:
                    env_content = f_read.read()
            
            if "ENCRYPTION_KEY=" not in env_content:
                with open(DOTENV_PATH, 'a') as f_append:
                    if env_content and not env_content.endswith('\n'):
                        f_append.write('\n')
                    f_append.write(f"ENCRYPTION_KEY={new_key_str}\n")
                print(f"A new ENCRYPTION_KEY has been generated and saved to: {DOTENV_PATH}")
            else:
                # This case implies ENCRYPTION_KEY= is in the file but perhaps empty or malformed,
                # so os.getenv didn't pick it up. We'll use the newly generated one.
                # Or, it could be a race condition if another process just wrote it.
                # For simplicity, we prioritize the one we just generated if os.getenv failed.
                # A more sophisticated approach might involve asking the user or re-reading.
                # However, if it's already there, we should probably respect it if load_dotenv can pick it up next time.
                # The current logic will append if "ENCRYPTION_KEY=" is not found.
                # If "ENCRYPTION_KEY=" IS found, but os.getenv failed, the user has a malformed .env.
                # We will use the new_key_str for this session.
                # The safest is to inform and use the new key.
                print(f"ENCRYPTION_KEY= line found in {DOTENV_PATH} but not loaded. Using newly generated key for this session.")
                print(f"Please check the format of ENCRYPTION_KEY in your .env file. It should be: ENCRYPTION_KEY=your_valid_key")


            encryption_key_str = new_key_str # Use the new key for the current session
            # Reload .env so os.getenv might pick up the new key if other parts of the script used os.getenv again.
            # For this script, explicitly setting encryption_key_str is primary.
            load_dotenv(dotenv_path=DOTENV_PATH, override=True) 
            
        except IOError as e:
            print(f"Error: Could not write to .env file at {DOTENV_PATH}. Error: {e}")
            print(f"Please manually create or update it with: ENCRYPTION_KEY={new_key_str}")
            print("Using the generated key for the current session only. It will not be saved.")
            encryption_key_str = new_key_str # Use the generated key in memory for this session
    else:
        print("Using existing ENCRYPTION_KEY from .env file.")

    # Ensure we have a key string to proceed
    if not encryption_key_str:
        print("Critical Error: No ENCRYPTION_KEY could be obtained or generated. Exiting.")
        sys.exit(1)

    try:
        encryption_key_bytes = encryption_key_str.encode('utf-8')
        # Basic validation: Fernet key must be 32 bytes, base64 encoded.
        # Fernet() constructor will raise an error if the key is invalid.
        from cryptography.fernet import Fernet
        Fernet(encryption_key_bytes) 
    except Exception as e:
        print(f"Error: The ENCRYPTION_KEY '{encryption_key_str[:10]}...' is invalid. Error: {e}")
        print("A valid Fernet key must be 32 url-safe base64-encoded bytes.")
        print(f"If this key was auto-generated, this error is unexpected. Please report it.")
        print(f"If you set this key manually, please ensure it is correct or remove it from {DOTENV_PATH} to regenerate.")
        sys.exit(1)

    # User Input
    client_id = input("Enter your Tesla Client ID: ").strip()
    client_secret = getpass.getpass("Enter your Tesla Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Client ID and Client Secret cannot be empty.")
        sys.exit(1)

    # Encryption
    credentials = {"client_id": client_id, "client_secret": client_secret}
    credentials_bytes = json.dumps(credentials).encode('utf-8')

    try:
        encrypted_credentials = encrypt_data(credentials_bytes, encryption_key_bytes)
    except Exception as e: # Catching broad exception as per prompt, could be more specific if needed
        print(f"Error during encryption: {e}")
        print("This might be due to an invalid ENCRYPTION_KEY format.")
        sys.exit(1)

    # Save Encrypted File
    try:
        with open(CREDENTIALS_FILE, "wb") as f:
            f.write(encrypted_credentials)
        print(f"Successfully encrypted credentials to: {CREDENTIALS_FILE}")
    except IOError as e:
        print(f"Error writing encrypted credentials to file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure scripts directory exists, though create_file_with_block should handle it.
    # For robustness, explicit check/creation could be added if not using that tool.
    if not SCRIPT_DIR.exists():
        SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    main()
