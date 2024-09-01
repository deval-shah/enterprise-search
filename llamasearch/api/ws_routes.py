
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import inject, Provide
from llamasearch.api.websocket_manager import get_websocket_manager
from llamasearch.api.core.security import get_current_user_ws
from llamasearch.api.core.container import Container
from llamasearch.api.db.session import get_db
from llamasearch.api.query_processor import process_query
from llamasearch.logger import logger
import os

ws_router = APIRouter()

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
        client_id = None
        session_id = None
        stream_response = True
        logger.info(f"WebSocket connection initiated. Pipeline factory: {pipeline_factory}")
        while True:
            data = await websocket.receive_json()
            if data['type'] == 'auth':
                try:
                    user, session_id = await get_current_user_ws(websocket, db, data.get('token'))
                    client_id = await websocket_manager.connect(websocket, user)
                    await websocket.send_json({"type": "authentication_success", "session_id": session_id})
                except Exception as e:
                    await websocket.send_json({"type": "authentication_failed", "content": str(e)})
                    break
            elif data['type'] == 'query':
                if not user or not session_id:
                    await websocket.send_json({"type": "error", "content": "Not authenticated"})
                    continue
                if data.get('session_id') != session_id:
                    await websocket.send_json({"type": "error", "content": "Invalid session"})
                    continue
                try:
                    stream_response = data.get('stream', True)  # Get streaming preference from query
                    file_paths = data.get('files', [])
                    result = await process_query(
                        query=data['query'],
                        user=user,
                        db=db,
                        pipeline_factory=pipeline_factory,
                        files_=file_paths
                    )
                    # Send metadata
                    await websocket.send_json({
                        "type": "metadata",
                        "context": result['context'],
                        "query": result['query'],
                        "file_upload": result['file_upload']
                    })
                    # Stream or send the response
                    await websocket_manager.stream_response(result['response'], client_id, stream=stream_response)
                
                except Exception as e:
                    logger.error(f"Query processing error: {str(e)}")
                    await websocket.send_json({"type": "error", "content": str(e)})
            else:
                await websocket.send_json({"type": "error", "content": "Unknown message type"})
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client: {client_id}")
        if client_id:
            await websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)