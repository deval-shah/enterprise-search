

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import json, requests

FIREBASE_API_KEY = "" # Firebase web key (from firebase console)
UID = "" # Firebase User ID
# Path to your service account credentials JSON file (from firebase console)
CRED_PATH = "/path/to/firebase.json"

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
    try:
        custom_token, id_token = generate_firebase_tokens(UID, CRED_PATH)
        print("Generated Firebase Custom Token:")
        print(custom_token)
        print("\nGenerated Firebase ID Token:")
        print(id_token)
        print("\nYou can use this ID token to authenticate with your server.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
