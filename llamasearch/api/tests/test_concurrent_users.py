import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
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
    firebase_api_key = "AIzaSyDjFrhSSLhC3AwJphgegzPtLvrQjwoafWI"
    auth_url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key={firebase_api_key}"
    response = requests.post(auth_url, json={
        "token": custom_token,
        "returnSecureToken": True
    })
    
    if response.status_code == 200:
        return response.json()['idToken']
    else:
        raise Exception("Failed to get ID token")

async def simultaneous_login(session, user_id):
    try:
        id_token = get_id_token(user_id)
        headers = {"Authorization": f"Bearer {id_token}"}
        async with session.post(f"{BASE_URL}/login", headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": f"Login failed with status {response.status}"}
    except Exception as e:
        return {"error": f"Exception during login: {str(e)}"}

async def rapid_login_logout(session, user_id, cycles):
    for _ in range(cycles):
        # Login
        id_token = get_id_token(user_id)
        headers = {"Authorization": f"Bearer {id_token}"}
        async with session.post(f"{BASE_URL}/login", headers=headers) as response:
            await response.json()
        # Immediate logout
        async with session.post(f"{BASE_URL}/logout") as response:
            await response.json()

async def access_protected_resource(session):
    async with session.get(f"{BASE_URL}/protected") as response:
        return await response.json()

def test_concurrent_users():
    async def run_tests():
        async with aiohttp.ClientSession() as session:
            # In the run_tests function:
            # print("\nTest 1: Simultaneous Login Attempts")
            user_ids = [uid, "1", "2", "3", "4", uid]
            login_tasks = [simultaneous_login(session, user_id) for user_id in user_ids]
            # login_results = await asyncio.gather(*login_tasks)
            # successful_logins = sum(1 for r in login_results if r and 'user' in r)
            # failed_logins = sum(1 for r in login_results if r and 'error' in r)
            # print(f"Simultaneous logins completed. Successful logins: {successful_logins}, Failed logins: {failed_logins}")
            # for result in login_results:
            #     if 'error' in result:
            #         print(f"Login error: {result['error']}")

            # Test 2: Session Collision Test
            # print("\nTest 2: Session Collision Test")
            # collision_tasks = [simultaneous_login(session, "collision_test_user") for _ in range(5)]
            # collision_results = await asyncio.gather(*collision_tasks)
            # unique_sessions = len(set(r.get('session_id') for r in collision_results if 'session_id' in r))
            # print(f"Unique sessions created: {unique_sessions}")

            # # Test 3: Rapid Login/Logout Cycle
            # print("\nTest 3: Rapid Login/Logout Cycle")
            # user_ids = [uid, "1", "2", "3", "4"]
            # cycle_tasks = [rapid_login_logout(session, i, 2) for i in user_ids]
            # await asyncio.gather(*cycle_tasks)
            # print("Rapid login/logout cycles completed")

            # Test 4: Concurrent Access to Shared Resources
            print("\nTest 4: Concurrent Access to Shared Resources")
            await asyncio.gather(*login_tasks)  # Ensure users are logged in
            access_tasks = [access_protected_resource(session) for _ in range(20)]
            access_results = await asyncio.gather(*access_tasks)
            print(access_results)
            successful_accesses = sum(1 for r in access_results if 'message' in r)
            print(f"Successful concurrent resource accesses: {successful_accesses}")

    asyncio.run(run_tests())

if __name__ == "__main__":
    test_concurrent_users()