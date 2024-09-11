import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_PATH = Path(os.getenv('APP_BASE_PATH', '.')).resolve()
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'keys/firebase.json')
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY', '')  # Add this to your .env file
UID = os.getenv('FIREBASE_TEST_UID', '')  # Add this to your .env file

CRED_PATH = BASE_PATH / FIREBASE_CREDENTIALS_PATH

def initialize_firebase(cred_path):
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

def generate_firebase_tokens(uid, cred_path):
    initialize_firebase(cred_path)

    # Generate a custom token
    custom_token = auth.create_custom_token(uid).decode('utf-8')

    # Exchange custom token for ID token
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"
    
    payload = json.dumps({
        "token": custom_token,
        "returnSecureToken": True
    })
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        id_token = response.json()['idToken']
        return custom_token, id_token
    else:
        raise Exception(f"Failed to exchange custom token for ID token: {response.text}")

if __name__ == "__main__":
    if not FIREBASE_API_KEY:
        print("ERROR: `FIREBASE_API_KEY` is not set in the .env file.")
        exit(1)

    if not UID:
        print("ERROR: `FIREBASE_TEST_UID` is not set in the .env file.")
        exit(1)

    try:
        custom_token, id_token = generate_firebase_tokens(UID, CRED_PATH)
        print("Generated Firebase Custom Token:")
        print(custom_token)
        print("\nGenerated Firebase ID Token:")
        print(id_token)
        print("\nYou can use this ID token to authenticate with your server.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")