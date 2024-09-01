import asyncio
import websockets
import json
import base64

WS_URL = "ws://localhost:8010/ws"
QUERY_URL = "http://localhost:8010/api/v1/query/"
AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImNlMzcxNzMwZWY4NmViYTI5YTUyMTJkOWI5NmYzNjc1NTA0ZjYyYmMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYWltbC1zaG9wLWVudGVycHJpc2VzZWFyY2giLCJhdWQiOiJhaW1sLXNob3AtZW50ZXJwcmlzZXNlYXJjaCIsImF1dGhfdGltZSI6MTcyMzYxNTE2OSwidXNlcl9pZCI6IlQwd0RQMUpHcm1kS1NaV1NSTEJQUkFUOHp2RTIiLCJzdWIiOiJUMHdEUDFKR3JtZEtTWldTUkxCUFJBVDh6dkUyIiwiaWF0IjoxNzIzNjE1MTY5LCJleHAiOjE3MjM2MTg3NjksImVtYWlsIjoiZGV2YWxAYWltbC50ZWFtIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbImRldmFsQGFpbWwudGVhbSJdfSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.B_SwuQAiLaDD5mKkiHnn7_RUt_e3QW4aaQWnNBLphQojZYptli7agqI-RlV4XtN2bwv7EC7h1ObmqRJQimG0zTv_A8-o7888O-J8VCfGI7HMXF1SbaXxk8aJOnUiaLTuwvffnPJlACHGKfm41h4qoKh7YZ244jir5X1UJRn5HXK8XvkxVbLO6fiz3jEGPwJzoRNyjkkwsZYNXMawgOgWt_clBxgooq4-qbW3pfgr_8RV-qzgo6HW8L-Fh9WR5Vlb4RX0EMl0eHbKsQZFo-k23L6R3GI2jlS3JYjEHSet8SXowBc8f48uSQB6ayIdZo8VUszLEb1do8YXPcl0R_8F9A"
FILES = ["./data/test_docs/Reduce_Hallucinations_RAG_Paper.pdf", "./data/test_docs/uber_10k-1-5.pdf"]

async def test_websocket_query(stream: bool):
    async with websockets.connect(WS_URL) as websocket:
        # Authenticate
        await websocket.send(json.dumps({
            "type": "auth",
            "token": f"Bearer {AUTH_TOKEN}"
        }))
        auth_response = await websocket.recv()
        print(f"Authentication response: {auth_response}")
        auth_data = json.loads(auth_response)
        if auth_data['type'] == "authentication_success":
            session_id = auth_data['session_id']
            print(f"Authentication successful. Session ID: {session_id}")
            # Send a query
            query_message = {
                "type": "query",
                "query": "What is RAG?",
                "stream": stream,
                "files": FILES,
                "session_id": session_id
            }
            await websocket.send(json.dumps(query_message))

            # Receive and process streamed response
            full_response = ""
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data["type"] == "chunk":
                    full_response += data["content"]
                elif data["type"] == "end_stream":
                    break
                elif data["type"] == "error":
                    print(f"Error: {data['content']}")
                    break
            print(f"Full response: {full_response}")
        elif auth_data['type'] == "authentication_failed":
            print(f"Authentication failed: {auth_data.get('content')}")
        else:
            print(f"Unexpected authentication response: {auth_data}")

if __name__ == "__main__":
     # Test with streaming
    print("\n--- Test with streaming mode ---\n")
    asyncio.run(test_websocket_query(stream=True))
    # Test without streaming
    print("\n--- Testing without streaming mode ---\n")
    asyncio.run(test_websocket_query(stream=False))