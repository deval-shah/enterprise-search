
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import inject, Provide
from llamasearch.api.websocket_manager import get_websocket_manager
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
        session_id = None
        query_data = None
        file_contents = []

        while True:
            message = await websocket.receive()
            logger.debug(f"Received message: {message['type']}")

            if message["type"] == "websocket.disconnect":
                break

            if message["type"] == "websocket.receive":
                if "text" in message:
                    data = json.loads(message["text"])
                    if data['type'] == 'auth':
                        user, session_id = await handle_auth(websocket, db, data)
                        client_id = await websocket_manager.connect(websocket, user)
                    elif data['type'] == 'query':
                        if not user or not session_id:
                            await websocket.send_json({"type": "error", "content": "Not authenticated"})
                            continue
                        query_data = WSQueryRequest(**data)
                        query_data.session_id = session_id  # Add session_id to the query data
                        result = await process_query_request(websocket, user, query_data, file_contents, db, pipeline_factory)
                        metadata = result.get("metadata", {})
                        response = result.get("response", "")
                        # Send metadata as a single JSON
                        await websocket.send_json(metadata)

                        # Stream the response
                        await websocket_manager.stream_response(response, user.firebase_uid)
                elif "bytes" in message:
                    logger.debug("Received binary data")
                    file_contents.append(message["bytes"])
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client: {user.firebase_uid if user else 'Unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

async def handle_auth(websocket, db, data):
    user, session_id = await get_current_user_ws(websocket, db, data.get('token'))
    await websocket.send_json({"type": "authentication_success", "session_id": session_id})
    return user, session_id

async def process_query_request(websocket, user, query_data: WSQueryRequest, file_contents, db, pipeline_factory):
    logger.info(f"Processing query request: {query_data.query}")
    try:
        pipeline = await pipeline_factory.get_or_create_pipeline_async(user.firebase_uid, user.tenant_id)
        user_upload_dir = pipeline.config.application.data_path

        file_data = []
        files_received = query_data.files or []

        for i, file_info in enumerate(files_received):
            if i < len(file_contents):
                file_data.append({
                    'filename': file_info['name'],
                    'content': file_contents[i]
                })

        file_upload_results = []
        if file_data:
            upload_results = await handle_file_upload(file_data, user_upload_dir)
            file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
            file_upload_results = upload_results
            logger.info(f"Files uploaded: {file_paths}")

        result = await process_query(
            query=query_data.query,
            user=user,
            db=db,
            pipeline_factory=pipeline_factory,
            file_paths=file_paths if file_data else None
        )
        res = {}
        res['metadata'] = {
            "type": "metadata",
            "context": result.get('context', []),
            "query": result.get('query', ''),
            "file_upload": file_upload_results
        }
        res['response'] = result.get('response', '')
        return res

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.firebase_uid}")
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}", exc_info=True)
        return {"type": "error", "content": str(e)}