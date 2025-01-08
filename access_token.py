import os
import requests
from datetime import datetime, timedelta, timezone
import json
from dotenv import load_dotenv

load_dotenv()

# Microsoft Authentication endpoints and credentials
TENANT_ID = os.getenv('TENANT_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TOKEN_FILE = "tokens.txt"

# Function to load tokens from a file
def load_tokens():
    """Loads tokens from a file."""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading tokens: {e}")
    return None


def save_tokens(tokens):
    """Saves tokens to a file."""
    try:
        # Calculate the expiration timestamp
        expiration_time = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        tokens["expires_at"] = expiration_time.timestamp()
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f)
    except Exception as e:
        print(f"Error saving tokens: {e}")


# Function to refresh tokens if expired
def refresh_access_token(tokens):
    """Refreshes the access token using the refresh token."""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "refresh_token": tokens["refresh_token"],
        "grant_type": "refresh_token",
        "client_secret": CLIENT_SECRET
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        new_tokens = response.json()
        save_tokens(new_tokens)
        return new_tokens["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error refreshing access token: {e}")
        return None


def get_access_token():
    """Gets a valid access token, refreshing it if necessary."""
    tokens = load_tokens()

    if not tokens:
        raise Exception("No tokens found. Please authenticate first.")

    access_token = tokens.get("access_token")
    expires_at = tokens.get("expires_at")  # Use the calculated expiration timestamp

    # Check if the token is expired
    if not expires_at or datetime.utcnow() >= datetime.fromtimestamp(expires_at):
        print("Access token expired, refreshing...")
        access_token = refresh_access_token(tokens)

    if not access_token:
        raise Exception("Unable to get a valid access token.")

    return access_token

