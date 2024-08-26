# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Union, Dict, Any
from functools import wraps
import json
# API Imports
from llamasearch.api.core.security import get_current_user, get_current_user_ws, get_optional_user, logout_user
from llamasearch.api.db.session import get_db
from llamasearch.api.schemas.user import UserInDB, User
from llamasearch.api.schemas.chat import ChatCreate, ChatResponse, ChatListResponse, MessageCreate, MessageResponse
from llamasearch.api.services.user import UserService
from llamasearch.api.services.chat import ChatService
from llamasearch.api.utils import handle_file_upload
from llamasearch.api.services.session import session_service
from llamasearch.api.core.config import settings
# Pipeline imports
from llamasearch.logger import logger
from llamasearch.api.core.container import Container
from llamasearch.pipeline import PipelineFactory, Pipeline
from llamasearch.api.websocket_manager import get_websocket_manager
from llamasearch.api.query_processor import process_query

router = APIRouter()
cookie_sec = APIKeyCookie(name="llamasearch_session")
security = HTTPBearer()

def standard_error_response(status_code: int, detail: str):
    return JSONResponse(
        status_code=status_code,
        content={"error": detail}
    )

def require_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user')
        if not user:
            return standard_error_response(401, "Unauthorized")
        return await func(*args, **kwargs)
    return wrapper

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, response, credentials, db)
    if user:
        if settings.USE_SESSION_AUTH:
            session_id = await session_service.create_session(db, user.id)
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite='lax',
                max_age=3600,
                domain=None  # Ensure this is set correctly for your domain
            )
        return {"message": "Logged in successfully", "user": user}
    else:
        return JSONResponse(content={"error": "Login failed"}, status_code=401)

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user_info: User = Depends(get_current_user)
):
    session_id = request.cookies.get("session_id")
    if user_info or session_id:
        await logout_user(request, response, user_info, db)
        return {"message": "Logged out successfully"}
    else:
        # User is already logged out or session expired
        return {"message": "No active session found"}

@router.post("/refresh-session")
async def refresh_session(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user:
        new_session_id = await session_service.create_session(db, user.id)
        response.set_cookie(
            key="session_id",
            value=new_session_id,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite='lax',
            max_age=3600,
        )
        return {"message": "Session refreshed successfully"}
    raise HTTPException(status_code=401, detail="Invalid session")

@router.get("/protected")
async def protected_route(request: Request, user_info: Tuple[User, bool] = Depends(get_current_user)):
    user, _ = user_info
    return {"message": f"Hello, {user.display_name or user.email}!"}

@router.get("/optional-auth")
async def optional_auth_route(request: Request, user_info: Optional[Tuple[Optional[User], bool]] = Depends(get_optional_user)):
    if user_info and user_info[0]:
        user, _ = user_info
        return {"message": f"Hello, {user.display_name or user.email}!"}
    else:
        return {"message": "Hello, anonymous user!"}

@router.post("/query/")
@inject
async def query_endpoint(
    request: Request,
    response: Response,
    query: str = Form(...),
    files: List[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory]),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Query endpoint called by user: {current_user.email}")
    try:
        result = await process_query(
            query=query,
            user=current_user,
            db=db,
            pipeline_factory=pipeline_factory,
            files=files
        )
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during processing the query: {query}")

@router.post("/uploadfile")
@inject
async def upload_files(
    files: List[UploadFile] = File(...),
    user_info: Tuple[User, bool] = Depends(get_current_user),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory])
):
    pipeline = await pipeline_factory.get_or_create_pipeline_async(user_info.firebase_uid, user_info.tenant_id)
    user_upload_dir = pipeline.config.application.data_path
    logger.debug(f"User Upload Dir: {user_upload_dir}")
    try:
        logger.info(f"Uploading {len(files)} files for user {user_info.firebase_uid}")
        upload_results = await handle_file_upload(files, user_upload_dir)
        file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
        logger.info("Inserting file paths : {}".format(file_paths))
        await pipeline.insert_documents(file_paths)
        return JSONResponse(content={"file_upload": upload_results}, status_code=200)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while uploading the files: {str(e)}")

@router.get("/recent-queries")
async def get_recent_queries(
    limit: int = 10,
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    recent_queries = await ChatService.get_recent_queries(db, user_info.firebase_uid, limit)
    return [
        {
            "query": log.query,
            "context": log.context,
            "response": log.response,
            "timestamp": log.timestamp
        } for log in recent_queries
    ]

# @router.post("/chats/", response_model=ChatResponse)
# @inject
# async def create_chat(
#     chat: ChatCreate,
#     user_info: Tuple[User, bool] = Depends(get_current_user)
# ):
#     try:
#         return await state_manager.create_chat(user_info.id, chat)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred while creating the chat: {str(e)}")

@router.get("/chats/", response_model=List[ChatListResponse])
async def read_chats(
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    user, _ = user_info
    return await ChatService.get_user_chats(db, user.id, skip, limit)

@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def read_chat(
    chat_id: str,
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ChatService.get_chat(db, chat_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Chat not found")

@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def add_message_to_chat(
    chat_id: str,
    message: MessageCreate,
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ChatService.add_message_to_chat(db, chat_id, message)
    except ValueError:
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while adding the message: {str(e)}")
    
@router.get("/me", response_model=UserInDB)
async def read_users_me(user_info: Tuple[UserInDB, bool] = Depends(get_current_user)):
    return user_info

@router.get("/user/{uid}", response_model=UserInDB)
async def read_user(uid: str, user_info: Tuple[User, bool] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_uid(db, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

