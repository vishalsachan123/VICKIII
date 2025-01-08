import os
import requests
from urllib.parse import urlencode
import json

# Microsoft Authentication endpoints and credentials
TENANT_ID = os.getenv('TENANT_ID')  # Replace with your tenant ID
CLIENT_ID = os.getenv('CLIENT_ID')  # Replace with your app's client ID
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Mail.ReadWrite", "Calendars.ReadWrite", "OnlineMeetings.ReadWrite","Chat.ReadWrite", "offline_access", 'Files.Read', 'Files.ReadWrite', 'Files.Read.All']
#SCOPES = ['Files.Read', 'Files.Read.All']
#SCOPES = ['OnlineMeetingTranscript.Read.All']
REDIRECT_URI = os.getenv('REDIRECT_URI')  # Replace with your redirect URI
CLIENT_SECRET = os.getenv('CLIENT_SECRET')  # Replace with your app's client secret

# Function to generate the authorization URL
def get_authorization_url():
    authorization_endpoint = f"{AUTHORITY}/oauth2/v2.0/authorize"
    
    # Prepare query parameters
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",  # We are requesting an authorization code
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(SCOPES),
        "state": "12345",  # This should be a randomly generated string for security purposes
    }

    # Generate the URL
    auth_url = f"{authorization_endpoint}?{urlencode(params)}"
    return auth_url

# Function to get the access and refresh tokens using the authorization code
def get_tokens_from_code(code):
    token_url = f"{AUTHORITY}/oauth2/v2.0/token"
    
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "scope": " ".join(SCOPES),
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens)  # Save tokens to the file
        return tokens
    else:
        raise Exception(f"Error fetching tokens: {response.text}")

# Function to save tokens to a text file
def save_tokens(tokens):
    with open("tokens.txt", 'w') as f:
        json.dump(tokens, f)

# Function to load tokens from a text file
def load_tokens():
    if os.path.exists("tokens.txt"):
        with open("tokens.txt", 'r') as f:
            return json.load(f)
    return None

# Main code for triggering user consent and getting an access token and refresh token
def main():
    print("Visit the following URL to give consent and get your authorization code:")
    print(get_authorization_url())
    print("After you approve the app, copy the authorization code from the URL and paste it here.")

    # Wait for the user to paste the authorization code here
    authorization_code = input("Enter the authorization code: ")
    try:
        tokens = get_tokens_from_code(authorization_code)
        print("Access and refresh tokens obtained successfully!")
        print(f"Access Token: {tokens['access_token']}")
        print(f"Refresh Token: {tokens['refresh_token']}")
    except Exception as e:
        print(f"Error obtaining tokens: {e}")

if __name__ == "__main__":
    main()
