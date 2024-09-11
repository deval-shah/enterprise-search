import requests
import firebase_admin
from firebase_admin import credentials, auth
import google.auth.transport.requests
import google.oauth2.id_token

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
uid = 'T0wDP1JGrmdKSZWSRLBPRAT8zvE2'
BASE_URL = "http://localhost:8010/api/v1"

def get_id_token(uid):
    # First, create a custom token
    custom_token = auth.create_custom_token(uid).decode('utf-8')
    
    # Exchange custom token for ID token
    # Note: In a real app, this would happen on the client side
    firebase_api_key = ""
    auth_url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key={firebase_api_key}"
    response = requests.post(auth_url, json={
        "token": custom_token,
        "returnSecureToken": True
    })

    if response.status_code == 200:
        return response.json()['idToken']
    else:
        raise Exception("Failed to get ID token")

def print_response(response):
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.text else 'No content'}")
    print("--------------------")

def test_auth_flow():
    session = requests.Session()

    # Scenario 1: First-time user login with Firebase ID token
    print("Scenario 1: First-time user login")
    id_token = get_id_token(uid)
    headers = {"Authorization": f"Bearer {id_token}"}
    response = session.post(f"{BASE_URL}/login", headers=headers)
    print_response(response)

    # Scenario 2: Logged-in user accessing protected route
    print("\nScenario 2: Logged-in user accessing protected route")
    response = session.get(f"{BASE_URL}/protected")
    print_response(response)

    # Scenario 3: Logged-in user accessing optional auth route
    print("\nScenario 3: Logged-in user accessing optional auth route")
    response = session.get(f"{BASE_URL}/optional-auth")
    print_response(response)

    # Scenario 4: Logout
    print("\nScenario 4: Logout")
    response = session.post(f"{BASE_URL}/logout")
    print_response(response)

    # Scenario 5: Accessing protected route after logout
    print("\nScenario 5: Accessing protected route after logout")
    response = session.get(f"{BASE_URL}/protected")
    print_response(response)

    # Scenario 6: Accessing optional auth route after logout
    print("\nScenario 6: Accessing optional auth route after logout")
    response = session.get(f"{BASE_URL}/optional-auth")
    print_response(response)

    # Scenario 7: Re-login after logout
    print("\nScenario 7: Re-login after logout")
    id_token = get_id_token(uid)
    headers = {"Authorization": f"Bearer {id_token}"}
    response = session.post(f"{BASE_URL}/login", headers=headers)
    print_response(response)

    # Scenario 8: Accessing user information
    print("\nScenario 8: Accessing user information")
    response = session.get(f"{BASE_URL}/me")
    print_response(response)

    # Scenario 9: Accessing another user's information (this might be restricted)
    print("\nScenario 9: Accessing another user's information")
    response = session.get(f"{BASE_URL}/user/1")
    print_response(response)

    # Scenario 10: Attempt to login with invalid token
    print("\nScenario 10: Attempt to login with invalid token")
    headers = {"Authorization": "Bearer invalid_token"}
    response = session.post(f"{BASE_URL}/login", headers=headers)
    print_response(response)

    session1 = requests.Session()
    session2 = requests.Session()
    # Test 11: Multiple logins (simulating different devices)
    print("\nTest 8: Multiple logins (simulating different devices)")
    id_token = get_id_token(uid)
    headers = {"Authorization": f"Bearer {id_token}"}
    response1 = session1.post(f"{BASE_URL}/login", headers=headers)
    response2 = session2.post(f"{BASE_URL}/login", headers=headers)
    print("Session 1:")
    print_response(response1)
    print("Session 2:")
    print_response(response2)

if __name__ == "__main__":
    test_auth_flow()
