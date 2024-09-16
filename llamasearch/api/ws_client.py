import asyncio
import websockets
import json
import base64
from tests.api.generate_token import generate_firebase_tokens

async def test_websocket():
    uri = "ws://localhost:8010/ws"
    custom_token, id_token = generate_firebase_tokens()
    
    try:
        async with websockets.connect(uri) as websocket:
            # Authenticate            
            await websocket.send(json.dumps({"type": "auth", "token": f"Bearer {id_token}"}))

            while True:
                response = await websocket.recv()
                data = json.loads(response)
                session_id = None
                if data["type"] == "authentication_success":
                    print(f"Authentication successful: {data}")
                    session_id = data["session_id"] if "session_id" in data else None
                    break
                elif data["type"] == "error":
                    print(f"Authentication error: {data}")
                    return

            # Send a query
            query_message = {
                "type": "query",
                "query": "What is the capital of France?",
                "stream": True,
                "session_id": session_id
            }
            await websocket.send(json.dumps(query_message))

            # Receive and print responses
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if data["type"] == "error":
                    print(f"Error: {data['content']}")
                    break
                elif data["type"] == "metadata":
                    print(f"Metadata: {data['content']}")
                elif data["type"] == "chunk":
                    print(f"Chunk: {data['content']}")
                elif data["type"] == "end_stream":
                    print("End of stream")
                    break
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"WebSocket connection closed unexpectedly: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

asyncio.get_event_loop().run_until_complete(test_websocket())
