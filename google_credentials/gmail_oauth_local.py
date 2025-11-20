import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def main():
    FILENAME = "credentials.json"
    flow = InstalledAppFlow.from_client_secrets_file(FILENAME, SCOPES)

    creds = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        prompt="consent",
        access_type="offline",
    )

    print(json.dumps({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }, indent=2))

if __name__ == "__main__":
    main()