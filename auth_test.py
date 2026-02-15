import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# This scope allows the bot to read your Drive files
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def run_auth():
    creds = None
    # Check if we already have a token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid token, let's log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This looks for the file you downloaded from Google Cloud
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the token for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Success! token.json has been created.")

if __name__ == '__main__':
    run_auth()
