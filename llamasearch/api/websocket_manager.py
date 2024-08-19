# websocket_manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, Callable, Optional, Tuple
import asyncio
import uuid
import json
from llamasearch.api.schemas.user import User
from llamasearch.logger import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Tuple[WebSocket, User]] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.users: Dict[str, User] = {}

    async def connect(self, websocket: WebSocket, user: User) -> str:
        client_id = user.firebase_uid
        self.active_connections[client_id] = (websocket, user)
        self.message_queues[client_id] = asyncio.Queue()
        self.users[client_id] = user
        return client_id

    def get_user(self, client_id: str) -> Optional[User]:
        connection = self.active_connections.get(client_id)
        return connection[1] if connection else None
    
    def get_connection(self, firebase_uid: str) -> Optional[Tuple[WebSocket, User]]:
        return self.active_connections.get(firebase_uid)

    async def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self.message_queues.pop(client_id, None)
        self.users.pop(client_id, None)
        logger.info(f"Client {client_id} disconnected")

    async def broadcast(self, message: str):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            await self.handle_disconnect(client_id)

    async def stream_response(self, response: str, client_id: str, stream: bool = True):
        if client_id not in self.active_connections:
            logger.error(f"Client {client_id} not found in active connections")
            return

        websocket, _ = self.active_connections[client_id]
        try:
            await websocket.send_json({"type": "start_stream"})
            if stream:
                for char in response:
                    await websocket.send_json({"type": "chunk", "content": char})
                    await asyncio.sleep(0.01)  # Small delay to simulate streaming
            else:
                await websocket.send_json({"type": "chunk", "content": response})
            await websocket.send_json({"type": "end_stream"})
        except WebSocketDisconnect:
            await self.handle_disconnect(client_id)
        except Exception as e:
            logger.error(f"Error streaming response for client {client_id}: {e}")
            await websocket.send_json({"type": "error", "content": str(e)})

    def _default_streamer(self, response: Any):
        if isinstance(response, str):
            yield response
        elif isinstance(response, dict):
            yield json.dumps(response)
        else:
            yield str(response)

    async def handle_client_messages(self, client_id: str):
        try:
            while True:
                message = await asyncio.wait_for(self.message_queues[client_id].get(), timeout=60)
                response = f"Response: {message}"
                await self.stream_response(response, client_id)
        except asyncio.TimeoutError:
            logger.error(f"No message received for client {client_id} in 60 seconds")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling messages for client {client_id}: {e}")
        finally:
            await self.handle_disconnect(client_id)

    async def process_messages(self, websocket: WebSocket, client_id: str):
        try:
            while True:
                data = await websocket.receive_text()
                await self.message_queues[client_id].put(data)
        except WebSocketDisconnect:
            await self.handle_disconnect(client_id)
        except Exception as e:
            logger.error(f"Error processing messages for client {client_id}: {e}")
            await self.handle_disconnect(client_id)

    async def handle_disconnect(self, client_id: str):
        self.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")

websocket_manager = ConnectionManager()

def get_websocket_manager():
    return websocket_manager