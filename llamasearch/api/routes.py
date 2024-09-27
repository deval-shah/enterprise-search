# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, Body, status
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Union, Dict, Any
from functools import wraps
import json, os
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
from llamasearch.api.core.redis import get_file_count, update_file_count
from llamasearch.pipeline import PipelineFactory, Pipeline
from llamasearch.api.websocket_manager import get_websocket_manager
from llamasearch.api.query_processor import process_query

router = APIRouter()
document_router = APIRouter(tags=["documents"])

cookie_sec = APIKeyCookie(name="llamasearch_session")
security = HTTPBearer()

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        if settings.ENABLE_AUTH:
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
async def protected_route(request: Request, user: User = Depends(get_current_user)):
    return {"message": f"Hello, {user.display_name or user.email}!"}

@router.get("/chats/", response_model=List[ChatListResponse])
async def read_chats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    return await ChatService.get_user_chats(db, user.id, skip, limit)

@router.get("/optional-auth")
async def optional_auth_route(request: Request, user: Optional[User] = Depends(get_optional_user)):
    if user:
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
    # Check for empty query
    if not query.strip():
        raise HTTPException(status_code=422, detail="Empty query string is not allowed")
    logger.info(f"Query endpoint called by user: {current_user.email}")
    try:
        pipeline = await pipeline_factory.get_or_create_pipeline_async(current_user.firebase_uid, current_user.tenant_id)
        user_upload_dir = pipeline.config.application.data_path

        file_paths = []
        if files:
            upload_results = await handle_file_upload(files, user_upload_dir)
            file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
            logger.info(f"Uploaded {len(file_paths)} files for query processing")

        result = await process_query(
            query=query,
            user=current_user,
            db=db,
            pipeline_factory=pipeline_factory,
            file_paths=file_paths
        )

        # Update file count in Redis
        update_file_count(current_user.firebase_uid, len(file_paths))

        return JSONResponse(content=result, status_code=200)
    except ValueError as ve:
        logger.error(f"Validation error in query processing: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during processing the query: {query}")

@router.post("/uploadfile")
@inject
async def upload_files(
    files: List[UploadFile] = File(...),
    user_info: User = Depends(get_current_user),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory])
):
    logger.info(f"Received upload request for {len(files)} files")
    if not files:
        logger.warning("No files provided in the request")
        raise HTTPException(status_code=422, detail="No file uploaded")

    for file in files:
        logger.info(f"Processing file: {file.filename}")
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}")

    pipeline = await pipeline_factory.get_or_create_pipeline_async(user_info.firebase_uid, user_info.tenant_id)
    user_upload_dir = pipeline.config.application.data_path
    logger.debug(f"User Upload Dir: {user_upload_dir}")

    try:
        upload_results = await handle_file_upload(files, user_upload_dir)
        successful_uploads = [result for result in upload_results if result['status'] == 'success']
        if not successful_uploads:
            raise HTTPException(status_code=400, detail="No files were successfully uploaded")

        file_paths = [result['location'] for result in successful_uploads]
        await pipeline.insert_documents(file_paths)

        return JSONResponse(content={"file_upload": upload_results}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while uploading the files: {str(e)}")


@document_router.post("/insert")
@inject
async def insert_documents(
    files: List[UploadFile] = File(...),
    user_info: User = Depends(get_current_user),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory]),
    db: AsyncSession = Depends(get_db)
):
    """
    Insert documents into the system.

    This endpoint allows users to upload and insert multiple documents into the system.
    It handles file upload, document insertion, and provides detailed feedback on the operation.

    Args:
        files (List[UploadFile]): List of files to be uploaded and inserted.
        user_info (User): Current authenticated user.
        pipeline_factory (PipelineFactory): Factory to create or get pipeline.
        db (AsyncSession): Database session.

    Returns:
        JSONResponse: A response containing the status of the insertion operation for each file.

    Raises:
        HTTPException: If an error occurs during the insertion process.
    """
    try:
        pipeline = await pipeline_factory.get_or_create_pipeline_async(user_info.firebase_uid, user_info.tenant_id)
        user_upload_dir = pipeline.config.application.data_path

        upload_results = await handle_file_upload(files, user_upload_dir)
        successful_uploads = [result for result in upload_results if result['status'] == 'success']

        if not successful_uploads:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "No files were successfully uploaded",
                    "data": upload_results
                }
            )

        file_paths = [result['location'] for result in successful_uploads]
        nodes = await pipeline.insert_documents(file_paths)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Documents successfully inserted",
                "data": [
                    {
                        "filename": os.path.basename(file_path),
                        "status": "inserted"
                    } for file_path in file_paths
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error inserting documents: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred while inserting documents: {str(e)}",
                "data": None
            }
        )

@document_router.delete("/delete", response_model=Dict[str, str])
@inject
async def delete_documents(
    filenames: List[str] = Body(..., description="List of filenames to delete"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory])
):
    """
    Delete documents based on provided filenames.

    Args:
        filenames (List[str]): List of filenames to delete.
        user (User): Current authenticated user.
        db (AsyncSession): Database session.
        pipeline_factory (PipelineFactory): Factory to create or get pipeline.

    Returns:
        Dict[str, str]: A dictionary with filenames as keys and deletion status as values.

    Raises:
        HTTPException: If an error occurs during the deletion process.
    """
    try:
        pipeline = await pipeline_factory.get_or_create_pipeline_async(user.firebase_uid, user.tenant_id)
        deletion_results = await pipeline.delete_documents(filenames)

        # Check if any files were not found
        not_found = [filename for filename, status in deletion_results.items() if status == "Not found"]
        if not_found:
            return JSONResponse(
                status_code=status.HTTP_207_MULTI_STATUS,
                content={"message": "Some files were not found", "results": deletion_results}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "All files deleted successfully", "results": deletion_results}
        )
    except Exception as e:
        logger.error(f"Error deleting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting documents: {str(e)}")


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

@router.get("/me", response_model=UserInDB)
async def read_users_me(user_info: Tuple[UserInDB, bool] = Depends(get_current_user)):
    return user_info

@router.get("/user/{uid}", response_model=UserInDB)
async def read_user(uid: str, user_info: Tuple[User, bool] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_uid(db, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# @router.post("/chats/", response_model=ChatResponse)
# @inject
# async def create_chat(
#     chat: ChatCreate,
#     user_info: Tuple[User, bool] = Depends(get_current_user)
# ):
#     try:
#         # TODO :: Add logic to create a chat
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred while creating the chat: {str(e)}")

# @router.get("/chats/{chat_id}", response_model=ChatResponse)
# async def read_chat(
#     chat_id: str,
#     user_info: Tuple[User, bool] = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         return await ChatService.get_chat(db, chat_id)
#     except ValueError:
#         raise HTTPException(status_code=404, detail="Chat not found")

# @router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
# async def add_message_to_chat(
#     chat_id: str,
#     message: MessageCreate,
#     user_info: Tuple[User, bool] = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         return await ChatService.add_message_to_chat(db, chat_id, message)
#     except ValueError:
#         raise HTTPException(status_code=404, detail="Chat not found")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred while adding the message: {str(e)}")

router.include_router(document_router, prefix="/documents")