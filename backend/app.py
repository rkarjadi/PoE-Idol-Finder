from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import Flask, request, redirect, session, jsonify, make_response
from flask_cors import CORS

import threading
import pprint
import requests
import os
import base64
import hashlib
import secrets
import csv
import re
from collections import defaultdict

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
cors = CORS(app, support_credentials=True, origins=["https://poe-idol-finder-1.onrender.com"])
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SESSION_COOKIE_NAME'] = 'poe_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

stash_items = None
idol_with_tags = None

load_dotenv()


CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPES = os.getenv('SCOPES').split(',')
SECRET_KEY = os.getenv("SECRET_KEY")
app.secret_key = SECRET_KEY

pp = pprint.PrettyPrinter(indent = 4)

def csv_to_list_of_dicts(csv_file):
    '''
        Reads a CSV file and returns a list of dictionaries
    '''
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]

    return data

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

    state = secrets.token_hex(16)
    code_verifier, code_challenge = generate_pkce_code()

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

    return auth_url, code_verifier, state

def exchange_code_for_token(client_id, client_secret, code, redirect_uri, code_verifier, scopes):
    """Exchanges an authorization code for an access token."""
    token_url = "https://www.pathofexile.com/oauth/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
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

def count_mods_by_content_tag(explicit_mods, idol_type):
    """Count explicit mods by content tag based on idol collection."""
    content_tag_counts = defaultdict(int)

    # Get idols based on idol type - create dictionary of affix to content tag
    idols = [idol for idol in csv_to_list_of_dicts('poe-idols.csv') if idol['Idol Type'] == idol_type]
    content_dict = {idol['Stripped Affix']: idol['Content Tag'] for idol in idols}

    # Replace the numbers in mod to #
    for mod in explicit_mods:
        mod = mod.replace('\n', ' ')
        if '%' in mod:
            re_mod = re.sub(r'\d+(\.\d+)?%', r'#%', mod, count=1)

        else:  
            re_mod = re.sub(r'\d+(\.\d+)?', r'#', mod, count=1)

        content_tag = content_dict.get(re_mod)

        if content_tag:
            content_tag_counts[content_tag] += 1

    return dict(content_tag_counts)  # Return the result as a dictionary

def add_content_tags_to_items(items):
    '''
        Gets the content tags of each item and adds it to a contentTag field
    '''

    for item in items:
        idol_type = item['baseType']
        explicit_mods = item['explicitMods']

        content_tags = count_mods_by_content_tag(explicit_mods, idol_type)
        item['contentTags'] = content_tags

    return items

@app.route("/is_authorized")
def is_authorized():
    '''
        Check if the user is authorized - if there is no access token, return False
    '''
    access_token = session.get('access_token')
    print(f"Checking session access token: {access_token}")
    print(f"Checking Session: {session}")

    if not access_token:

        res = make_response(jsonify({"authorized": False}))
        res.headers['Access-Control-Allow-Origin'] = 'https://poe-idol-finder-1.onrender.com'
        res.headers['Access-Control-Allow-Credentials'] = 'true'
        return res
    
    else:

        res = make_response(jsonify({"authorized": True}))
        res.headers['Access-Control-Allow-Origin'] = 'https://poe-idol-finder-1.onrender.com'
        res.headers['Access-Control-Allow-Credentials'] = 'true'
        return res

@app.route("/authorize")
def authorize():
    '''
        Prompts the user to authorize the project
    '''

    client_id = CLIENT_ID
    redirect_uri = REDIRECT_URI
    scopes = SCOPES
    auth_url, session["code_verifier"], session["state"] = generate_auth_url(client_id, redirect_uri, scopes)

    return redirect(auth_url)


@app.route("/callback")
def oauth_callback():
    '''
        Callback function to get access token and redirect to frontend
    '''

    code_verifier = session.get('code_verifier')
    state = session.get('state')

    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    redirect_uri = REDIRECT_URI
    scopes = SCOPES

    print("Callback function triggered!")
    print("Received request args:", request.args)

    received_code = request.args.get("code")
    received_state = request.args.get("state")

    print(f"Global state: {state}")

    print(f"Received state: {received_state}")

    if received_state != session.get('state'):
        print("Error: State mismatch.")
        return "Error: State mismatch! Possible CSRF attack.", 400

    # Exchange the code for tokens
    tokens = exchange_code_for_token(client_id, client_secret, received_code, redirect_uri, code_verifier, scopes)

    print("Access Token:", tokens)
    session['access_token'] = tokens.get("access_token")
    session['refresh_token'] = tokens.get('refresh_token')
    session.modified = True
    
    # Redirect to home page
    return redirect("https://poe-idol-finder-1.onrender.com")

@app.route("/logout")
def logout():
    '''
        Removes tokens and state from session
    '''
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    session.pop('state', None)
    return redirect("https://poe-idol-finder.onrender.com/is_authorized")

@app.route("/get_stashes")
def get_stashes():
    '''
        Gets all stashes from PoE API
    '''

    access_token = session.get('access_token')
    print(f"Checking session: {session}")

    if not access_token:
        return "Error: No access token found. Please authorize first.", 400

    headers = {
    'Authorization': f'Bearer {access_token}',
    "User-Agent": f"OAuth {CLIENT_ID}/1.0.0 (contact: rkarjadi@bu.edu)"
    }

    r = requests.get("https://api.pathofexile.com/stash/phrecia", headers=headers)

    if r.status_code == 200:
        stashes = r.json()['stashes']
        stash_list = []

        for stash in stashes:
            if stash["type"] == "Folder":
                for substash in stash["children"]:
                    stash_list.append({"name": substash["name"], "id": substash["id"], "type": substash["type"]})

            else:
                stash_list.append({"name":stash["name"], "id": stash["id"], "type": stash["type"]})

        res = make_response(jsonify(stash_list))
        res.headers['Access-Control-Allow-Origin'] = 'https://poe-idol-finder-1.onrender.com'
        res.headers['Access-Control-Allow-Credentials'] = 'true'
        return res


    else:
        return f"Error: {r.status_code} - {r.text}", 400

@app.route("/get_stash/<stash_id>")
def get_stash(stash_id):
    '''
        Gets stash content from PoE API - NOT USED
    '''

    access_token = session.get('access_token')
    if not access_token:
        return "Error: No access token found. Please authorize first.", 400

    headers = {
    'Authorization': f'Bearer {access_token}',
    "User-Agent": f"OAuth {CLIENT_ID}/1.0.0 (contact: rkarjadi@bu.edu)"
    }

    r = requests.get(f"https://api.pathofexile.com/stash/phrecia/{stash_id}", headers=headers)

    if r.status_code == 200:
        return r.json()

    else:
        return f"Error: {r.status_code} - {r.text}", 400

@app.route("/get_idols_with_content_tags/<stash_id>")
def get_idols_with_content_tags(stash_id):
    '''
        Gets all idols from a stash with content tags
    '''

    global idol_with_tags

    access_token = session.get('access_token')

    if not access_token:
        return "Error: No access token found. Please authorize first.", 400

    headers = {
    'Authorization': f'Bearer {access_token}',
    "User-Agent": f"OAuth {CLIENT_ID}/1.0.0 (contact: rkarjadi@bu.edu)"
    }

    r = requests.get(f"https://api.pathofexile.com/stash/phrecia/{stash_id}", headers=headers)

    if r.status_code == 200:
        stash_items = r.json()

    else:
        return f"Error: {r.status_code} - {r.text}", 400

    items = stash_items.get('stash', {}).get('items', [])

    idols = [item for item in items if 'Idol' in item['typeLine'] and item['rarity'] != 'Unique']

    if idols == []:
        res = make_response(jsonify([]))
        res.headers['Access-Control-Allow-Origin'] = 'https://poe-idol-finder-1.onrender.com'
        res.headers['Access-Control-Allow-Credentials'] = 'true'

        return res


    for idol in idols:
        idol_type = idol['baseType']
        explicit_mods = idol['explicitMods']

        content_tags = count_mods_by_content_tag(explicit_mods, idol_type)
        idol['contentTags'] = content_tags

    idol_with_tags = idols

    res = make_response(jsonify(idol_with_tags))
    res.headers['Access-Control-Allow-Origin'] = 'https://poe-idol-finder-1.onrender.com'
    res.headers['Access-Control-Allow-Credentials'] = 'true'

    return res

if __name__ == "__main__":
    app.run()
