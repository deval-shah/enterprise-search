# Enterprise Search API

## Authentication

### Generate User Token

Setup firebase credentials and set values by following the instructions in [firebase](docs/firebase.md) file.

```bash
FIREBASE_CREDENTIALS_PATH=keys/firebase.json # Path to Firebase Credentials file
FIREBASE_API_KEY= # Firebase Web API Key
FIREBASE_TEST_UID= # Firebase Test UID
```

Update these values in `.env` file in the root directory.

```bash
python tests/api/generate_token.py
export FIREBASE_ID_TOKEN=eyJhbGciOiJSUz... # Export the generated Firebase ID token to this variable for convenience to use in curl commands
```

## API Documentation

To explore and interact with the ES API using Swagger UI:

1. Start the ES API server
2. Open your web browser and navigate to:
   `http://localhost:8010/api/v1/docs`

This will provide you with a comprehensive, interactive documentation of all available endpoints, request/response models, and the ability to test the API directly from your browser.

For a more detailed, non-interactive view of the API specification, you can also access the ReDoc version at:
`http://localhost:8010/api/v1/redoc`

## API Testing

Use the cURL commands shared below to test the API endpoints.

### 1. Login and Generate Cookies (Authentication)
Use the following curl command to log in and generate the cookies.txt file:

```bash
curl -i -X POST http://localhost:8010/api/v1/login \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN" \
  -c cookies.txt
```

Replace `YOUR_FIREBASE_ID_TOKEN` with the token you got from step 1.

This command will create a `cookies.txt` file in your current directory.

### 2. Before testing API using curl commands
1. Default values are provided for testing. Replace `query`, `files`" with your data in the curl commands.
2. Ensure `cookies.txt` is in your working directory or specify its full path.
3. Adjust server URL if not using `localhost:8010`.

*Note: These steps are important for successful API testing with cURL.*

### 3. Query Endpoints

1. Query (without file upload)
```bash
curl -X POST http://localhost:8010/api/v1/query/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=What is RAG?" \
  -b cookies.txt
```

2. Query (with single file upload)
```bash
curl -X POST http://localhost:8010/api/v1/query/ \
  -H "Content-Type: multipart/form-data" \
  -F "query=How many heads are used in the multi-head attention mechanism of the base Transformer model?" \
  -F "files=@data/test_docs/attention_is_all_you_need.pdf" \
  -b cookies.txt
```

<div align="center">
  <img src="../assets/life-of-a-request.png" alt="Life of a Query Request (with file upload)" width="800" />
  <p>
    <em>Life of a request - query with file upload</em>
  </p>
</div>

3. Query (with multiple file uploads)
```bash
curl -X POST http://localhost:8010/api/v1/query/ \
  -H "Content-Type: multipart/form-data" \
  -F "query=What BLEU score did the big Transformer model achieve on the WMT 2014 English-to-German translation task?" \
  -F "files=@data/test_docs/attention_is_all_you_need.pdf" \
  -F "files=@data/test_docs/meta_10k.pdf" \
  -b cookies.txt
```

### 4. File Operations Endpoints

4. Upload file(s) (Same as insert endpoint, will be deprecated in future)
```bash
curl -X POST http://localhost:8010/api/v1/uploadfile \
  -H "Content-Type: multipart/form-data" \
  -F "files=@data/test_docs/adelaide_strategic_plan_2024_2028.pdf" \
  -F "files=@data/test_docs/meta_10k.pdf" \
  -b cookies.txt
```

5. Insert single file
```bash
curl -X POST http://localhost:8010/api/v1/documents/insert \
  -H "Content-Type: multipart/form-data" \
  -F "files=@data/test_docs/adelaide_strategic_plan_2024_2028.pdf" \
  -b cookies.txt
```

6. Insert multiple files
```bash
curl -X POST http://localhost:8010/api/v1/documents/insert \
  -H "Content-Type: multipart/form-data" \
  -F "files=@data/test_docs/meta_10k.pdf" \
  -F "files=@data/test_docs/attention_is_all_you_need.pdf" \
  -b cookies.txt
```

7. Delete file
```bash
curl -X DELETE http://localhost:8010/api/v1/documents/delete \
  -H "Content-Type: application/json" \
  -d '{"filenames": ["meta_10k.pdf", "attention_is_all_you_need.pdf"]}' \
  -b cookies.txt
```

### 5. User Endpoints

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

## 6. WebSocket Endpoints

Test the WebSocket API using the client script. Run from the project root directory:

```bash
python -m llamasearch.api.ws_client
```

This client demonstrates how to authenticate, send a query, and receive a streamed response using the WebSocket API.

Refer test scripts in `tests/api/test_api_websocket.py` for more ways to use the WebSocket API endpoints.