from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import Flask, request, redirect

import threading
import pprint
import requests
import os
import base64
import hashlib
import secrets

app = Flask(__name__)

global_code_verifier = None
stored_state = None
code_verifier = None

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')

pp = pprint.PrettyPrinter(indent = 4)

def base64_url_encode(url):
    '''
        Encodes bytes in URL-safe Base64 w.o padding
    '''
    return base64.urlsafe_b64encode(url).rstrip(b'=').decode('utf-8')

def generate_pkce_code():
    '''
        Generates PKCE code verifier & challenge
    '''
    code_verifier = base64_url_encode(os.urandom(32))
    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64_url_encode(sha256_hash)
    return code_verifier, code_challenge

def generate_auth_url(client_id, redirect_uri, scopes):
    '''
        Generates OAuth 2.0 URL for PoE
    '''
    global global_code_verifier

    state = secrets.token_hex(16)
    code_verifier, code_challenge = generate_pkce_code()
    global_code_verifier = code_verifier

    base_url = "https://www.pathofexile.com/oauth/authorize"
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(scopes),
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }

    auth_url = f"{base_url}?{urlencode(params)}"
    # auth_url = f"{base_url}?{urlencode(params)}&redirect_uri={redirect_uri}"
    return auth_url, code_verifier, state

@app.route("/callback")
def oauth_callback():
    global global_code_verifier

    print("Callback function triggered!")
    print("Received request args:", request.args)

    received_code = request.args.get("code")
    received_state = request.args.get("state")

    if not received_code:
        print("Error: No code received.")
        return "Error: No authorization code received.", 400

    if not received_state:
        print("Error: State mismatch.")
        return "Error: State mismatch! Possible CSRF attack.", 400

    # Exchange the code for tokens
    tokens = exchange_code_for_token(client_id, received_code, redirect_uri, global_code_verifier, scopes)

    print("Access Token:", tokens)

    return f"Access Token: {tokens['access_token']}<br>Refresh Token: {tokens.get('refresh_token')}"


def exchange_code_for_token(client_id, code, redirect_uri, code_verifier, scopes):
    """Exchanges an authorization code for an access token."""
    token_url = "https://www.pathofexile.com/oauth/token"

    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "code_verifier": code_verifier
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"OAuth {client_id}/1.0.0 (contact: rkarjadi@bu.edu)"
    }

    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code == 200:
        return response.json()  # Returns access_token, refresh_token, etc.
    else:
        return {"error": f"Token exchange failed: {response.status_code} - {response.text}"}

# Start the Flask server in a separate thread
def run_flask():
    app.run(host="localhost", port=5000)

if __name__ == "__main__":
    client_id = CLIENT_ID
    redirect_uri = "http://localhost:5000/callback"
    scopes = ["account:stashes", "account:leagues"]

    auth_url = generate_auth_url(client_id, redirect_uri, scopes)
    print(f"Visit this URL to authorize:\n{auth_url}")

    # Start Flask in a separate thread
    # threading.Thread(target=run_flask, daemon=True).start()
    run_flask()


    # # Generate the authorization URL
    # auth_url = generate_auth_url(client_id, redirect_uri, scopes)
    # print(f"Visit this URL to authorize:\n{auth_url}")