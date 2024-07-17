## Firebase Setup
We are using Firebase to authenticate users on the ES server and UI.

### Get Service Account Credentials JSON

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click "Project settings" (gear icon)
4. Go to "Service Accounts" tab
5. Click "Generate new private key"
6. Confirm by clicking "Generate key"
7. Save the downloaded JSON file securely

### Get Firebase API Key

1. In Firebase Console, go to "Project settings"
2. Under "General" tab, scroll to "Your apps" section
3. Find your app (or create one if none exists)
4. Copy the "Web API Key" value

### Get User ID for Testing

1. **Create a test user**:
   - Go to Firebase Console > Authentication > Users
   - Click "Add user"
   - Enter an email and password
   - Save the user

2. **Get the User UID**:
   - In the Users list, find your newly created user
   - Copy the "User UID" value

Use these credentials in your [generate_token.py](llamasearch/api/tests/generate_token.py) script and API requests.
