
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import inject, Provide
from llamasearch.api.websocket_manager import get_websocket_manager, WSMessage, WSStreamChunk, WSMetadata, WSEndStream
from llamasearch.api.core.security import get_current_user_ws
from llamasearch.api.core.container import Container
from llamasearch.api.db.session import get_db
from llamasearch.api.query_processor import process_query
from llamasearch.logger import logger
from llamasearch.api.utils import handle_file_upload
import asyncio
import os
import json
from pydantic import BaseModel
from typing import List, Optional, Dict, Union, Any
from collections import defaultdict

ws_router = APIRouter()

class WSQueryRequest(BaseModel):
    query: str
    files: Optional[List[Dict[str, Union[str, bytes]]]] = None
    session_id: str

class WSQueryResponse(BaseModel):
    type: str
    content: Union[str, Dict[str, Any]]

@ws_router.websocket("/ws")
@inject
async def websocket_endpoint(
    websocket: WebSocket, 
    db: AsyncSession = Depends(get_db),
    pipeline_factory = Depends(Provide[Container.pipeline_factory])
):
    try:
        websocket_manager = get_websocket_manager()
        await websocket.accept()
        user = None
        client_id = None

        while True:
            message = await websocket.receive()
            #logger.debug(f"Received message type: {message['type']}")

            if message["type"] == "websocket.disconnect":
                break

            if message["type"] == "websocket.receive":
                data = json.loads(message["text"])

                if data['type'] == 'auth':
                    user, session_id = await handle_auth(websocket, db, data)
                    client_id = await websocket_manager.connect(websocket, user)

                elif data['type'] == 'query':
                    if not user or not client_id:
                        await websocket.send_json({"type": "error", "content": "Not authenticated"})
                        continue

                    query_data = WSQueryRequest(**data)
                    files = data.get('files', [])

                    # Validate file data
                    invalid_files = [file for file in files if not file.get('content')]
                    if invalid_files:
                        error_response = {
                            "type": "error",
                            "content": {
                                "error": "Invalid file data",
                                "invalid_files": [file['name'] for file in invalid_files]
                            }
                        }
                        await websocket.send_json(error_response)
                        continue

                    result = await process_query_request(websocket, user, query_data, files, db, pipeline_factory, client_id)
    
                    # Send metadata
                    await websocket.send_json(WSMetadata(content=result.content["metadata"]).dict()) 
                    # Stream response
                    response = result.content["response"]
                    for chunk in response.split():  # Split response into words for demonstration
                        await websocket.send_json(WSStreamChunk(content=chunk).dict())
                    # Send end of stream
                    await websocket.send_json(WSEndStream().dict())

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client: {client_id if client_id else 'Unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

async def handle_auth(websocket, db, data):
    user, session_id = await get_current_user_ws(websocket, db, data.get('token'))
    await websocket.send_json({"type": "authentication_success", "session_id": session_id})
    return user, session_id

async def process_query_request(websocket, user, query_data: WSQueryRequest, files, db, pipeline_factory, client_id):
    logger.info(f"Processing query request for client {client_id}: {query_data.query}")
    try:
        pipeline = await pipeline_factory.get_or_create_pipeline_async(user.firebase_uid, user.tenant_id)
        user_upload_dir = pipeline.config.application.data_path
        file_upload_results = []
        file_paths = []
        if files:
            logger.info(f"{len(files)} file(s) received for client {client_id}")
            upload_results = await handle_file_upload(files, user_upload_dir)
            file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
            file_upload_results = upload_results
            logger.debug(f"Files uploaded for client {client_id}: {file_paths}")
        else:
            logger.info(f"No files received for client {client_id}")
        result = await process_query(
            query=query_data.query,
            user=user,
            db=db,
            pipeline_factory=pipeline_factory,
            file_paths=file_paths
        )
        response = WSQueryResponse(
            type="query_response",
            content={
                "response": result.get('response', ''),
                "metadata": {
                    "query": query_data.query,
                    "context": result.get('context', []),
                    "file_upload": file_upload_results
                }
            }
        )
        return response
    except Exception as e:
        logger.error(f"Query processing error for client {client_id}: {str(e)}")
        return WSQueryResponse(
            type="error",
            content={
                "response": '',
                "metadata": {
                    "error": str(e),
                    "query": query_data.query,
                    "context": result.get('context', []),
                    "file_upload": []
                }
            }
        )