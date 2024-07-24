# LlamaSearch API Curl Commands

## Authentication

### Generate User Token

Get firebase credentials and values by following the instructions in [firebase](docs/firebase.md) file.

```bash
FIREBASE_CREDENTIALS_PATH=keys/firebase.json # Path to Firebase Credentials file
FIREBASE_API_KEY= # Firebase Web API Key
FIREBASE_TEST_UID= # Firebase Test UID
```

Update these values in `.env` file in the root directory.

```bash
python llamasearch/api/tests/generate_token.py
```
This will output a Firebase ID token. Copy this token for use in the login request.

## API Testing Options

You have two options for testing the LlamaSearch APIs:

1. **Postman**: A collection is available for API testing. To gain access to the Postman collection, please contact the project owner.

2. **cURL Commands**: Alternatively, you can use the cURL commands provided below for command-line testing.

Currently, we do not support `chat` endpoints.

### Option 1: Postman

[<img src="https://run.pstmn.io/button.svg" alt="Run in Postman" style="width: 128px; height: 32px;">](https://null.postman.co/collection/33701240-3cfdeb70-981a-446d-b4e0-0da98b71e936?source=rip_markdown)

### 1. Setup: Set environment variables in Postman:
   - `base_url`: Your server URL (e.g., "http://localhost:8010")
   - `firebase_id_token`: A valid Firebase ID token
   - `auth_cookie`, `uid`, `chat_id`: Initialize as empty strings (not required for login) 

### 2. Authentication
- First, send the "Login" POST request to `/api/v1/login`
- It will create cookies.txt and store it for endpoint calls.

Once login is successful, start testing the endpoints.

### Option 2: cURL Commands

### 1. Login and Generate Cookies
Use the following curl command to log in and generate the cookies.txt file:

```bash
curl -i -X POST http://localhost:8010/api/v1/login \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -c cookies.txt
```

Replace `YOUR_FIREBASE_ID_TOKEN` with the token you got from step 1.

This command will create a `cookies.txt` file in your current directory.

### Before testing API using curl commands
1. Replace placeholders (e.g., "Your query text here", file paths) with actual data.
2. Ensure `cookies.txt` is in your working directory or specify its full path.
3. Adjust server URL if not using `localhost:8010`.

Note: These steps are important for successful API testing with cURL.

## Query Endpoints

1. Query (without file upload)
```bash
curl -X POST http://localhost:8010/api/v1/query/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=Your query text here" \
  -b cookies.txt
```

2. Query (with single file upload)
```bash
curl -X POST http://localhost:8010/api/v1/query/ \
  -H "Content-Type: multipart/form-data" \
  -F "query=Your query text here" \
  -F "files=@data/sample-docs/test.pdf" \
  -b cookies.txt
```

3. Query (with multiple file uploads)
```bash
curl -X POST http://localhost:8010/api/v1/query/ \
  -H "Content-Type: multipart/form-data" \
  -F "query=Your query text here" \
  -F "files=@data/sample-docs/test1.pdf" \
  -F "files=@data/sample-docs/test2.pdf" \
  -b cookies.txt
```

## File Upload Endpoints

4. Upload single file
```bash
curl -X POST http://localhost:8010/api/v1/uploadfile \
  -H "Content-Type: multipart/form-data" \
  -F "files=@data/sample-docs/test.pdf" \
  -b cookies.txt
```

5. Upload multiple files
```bash
curl -X POST http://localhost:8010/api/v1/uploadfile \
  -H "Content-Type: multipart/form-data" \
  -F "files=@data/sample-docs/test1.pdf" \
  -F "files=@data/sample-docs/test2.pdf" \
  -b cookies.txt
```

## User Endpoints

Replace {uid} with an actual user ID.

6. Get current user info
```bash
curl -X GET http://localhost:8010/api/v1/me \
  -b cookies.txt
```

7. Get user by UID
```bash
curl -X GET http://localhost:8010/api/v1/user/{uid} \
  -b cookies.txt
```
## Other Endpoints (unstable)

8. Get recent queries
```bash
curl -X GET "http://localhost:8010/api/v1/recent-queries?limit=10" \
  -b cookies.txt
```

9. Create a new chat
```bash
curl -X POST http://localhost:8010/api/v1/chats/ \
  -H "Content-Type: application/json" \
  -d '{"title": "New Chat Title"}' \
  -b cookies.txt

```
10. Get list of chats
```bash
curl -X GET "http://localhost:8010/api/v1/chats/?skip=0&limit=10" \
  -b cookies.txt

```

11. Get a specific chat
```bash
curl -X GET http://localhost:8010/api/v1/chats/{chat_id} \
  -b cookies.txt
```
Replace {chat_id} with an actual chat ID.

12. Add a message to a chat
```bash
curl -X POST http://localhost:8010/api/v1/chats/{chat_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Your message content here"}' \
  -b cookies.txt
```
Replace {chat_id} with an actual chat ID.