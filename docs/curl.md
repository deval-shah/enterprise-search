# LlamaSearch API Curl Commands

## Authentication

### 1. Generate User Token

Get firebase credentials and values by following the instructions in [firebase](docs/firebase.md) file.

```bash
FIREBASE_API_KEY = "" # Firebase web key
UID = "" # Firebase User ID
CRED_PATH = "" # Credentials file
```

Update constant values in the [generate_token.py](llamasearch/api/tests/generate_token.py) script and API requests.

```bash
python llamasearch/api/tests/generate_token.py
```
This will output a Firebase ID token. Copy this token for use in the login request.

### 2. Login and Generate Cookies
Use the following curl command to log in and generate the cookies.txt file:

```bash
curl -i -X POST http://localhost:8010/api/v1/login \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -c cookies.txt
```

Replace `YOUR_FIREBASE_ID_TOKEN` with the token you got from step 1.

This command will create a `cookies.txt` file in your current directory and show the response headers and body. Use it to authenticate your requests to the backend api server.

### Before testing API using curl commands
- Replace placeholder text (like "Your query text here" or file paths) with your actual data.
- Ensure that the `cookies.txt` file is in the same directory as where you're running the curl command, or provide the full path to the file.
- These commands assume your server is running on `localhost:8010`. Adjust the URL if your server is running on a different host or port.

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