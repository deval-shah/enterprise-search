# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response, File, UploadFile, Form, BackgroundTasks
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Union
# API Imports
from llamasearch.api.core.security import get_current_user, get_optional_user, logout_user
from llamasearch.api.db.session import get_db
from llamasearch.api.schemas.user import UserInDB, User
from llamasearch.api.schemas.chat import ChatCreate, ChatResponse, ChatListResponse, MessageCreate, MessageResponse
from llamasearch.api.services.user import UserService
from llamasearch.api.services.chat import ChatService
from llamasearch.api.utils import handle_file_upload, get_user_upload_dir
from llamasearch.api.tasks import log_query_task
from llamasearch.api.services.session import session_service
# Pipeline imports
from llamasearch.logger import logger
from llamasearch.utils import profile_
from llamasearch.api.core.container import Container
from llamasearch.pipeline import PipelineFactory, Pipeline

from dependency_injector.wiring import inject, Provide

router = APIRouter()
cookie_sec = APIKeyCookie(name="llamasearch_session")
security = HTTPBearer()

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        user, is_new_session = await get_current_user(request, response, credentials, db)
        return {
            "message": "Logged in successfully" if is_new_session else "Already logged in",
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = request.cookies.get("session_id")
    user = None
    if session_id:
        user = await session_service.get_user_session(db, session_id)
    await logout_user(request, response, user, db)
    if user:
        logger.info(f"User {user.id} logged out successfully")
    else:
        logger.info("Logged out (no active user session)")
    return {"message": "Logged out successfully"}

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
async def query_index(
    query: str = Form(...),
    user_info: Tuple[User, bool] = Depends(get_current_user),
    files: Union[UploadFile, List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory])
):
    logger.debug(f"Received query: {query}")
    user, _ = user_info
    pipeline = await pipeline_factory.get_or_create_pipeline_async(user.firebase_uid)
    try: 
        file_upload_response = []
        if files:
            upload_results = await handle_file_upload([files] if isinstance(files, UploadFile) else files, user.firebase_uid)
            file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
            await pipeline.insert_documents(file_paths)
        else:
            logger.debug("No files received")
        response = await pipeline.perform_query_async(query)
        logger.debug(f"Raw response from query_app: {response}")
        if response is None or not hasattr(response, 'response'):
            raise ValueError(f"Invalid response from query processing {response}.")
        document_info, retrieval_context = Pipeline.get_context_from_response(response)
        context_details = [
            {
                "file_path": path,
                "file_name": details['file_name'],
                "last_modified": details['last_modified_date'],
                "document_id": details['doc_id']
            }
            for path, details in document_info.items()
        ]
        logger.debug("Context details: " + str(context_details))
        # Log query in db
        try:
            await log_query_task(db, user.firebase_uid, query, context_details, response.response)
        except Exception as e:
            logger.error(f"Failed to log query for user {user.firebase_uid}: {str(e)}")

        return JSONResponse(content={
            "response": response.response,
            "context": context_details,
            "query": query,
            "file_upload": file_upload_response
        }, status_code=200)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during processing the query: {query}")

@router.post("/uploadfile")
@inject
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: Tuple[User, bool] = Depends(get_current_user),
    pipeline_factory: PipelineFactory = Depends(Provide[Container.pipeline_factory])
):
    user, _ = current_user
    pipeline = await pipeline_factory.get_or_create_pipeline_async(user.firebase_uid)
    try:
        logger.info(f"Uploading {len(files)} files for user {user.firebase_uid}")

        upload_results = await handle_file_upload(files, user.firebase_uid)
        file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
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
    current_user: Tuple[User, bool] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, _ = current_user
    recent_queries = await ChatService.get_recent_queries(db, user.firebase_uid, limit)
    return [
        {
            "query": log.query,
            "context": log.context,
            "response": log.response,
            "timestamp": log.timestamp
        } for log in recent_queries
    ]

@router.post("/chats/", response_model=ChatResponse)
async def create_chat(
    chat: ChatCreate,
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, _ = user_info
    try:
        return await ChatService.create_chat(db, user.id, chat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the chat: {str(e)}")

@router.get("/chats/", response_model=List[ChatListResponse])
async def read_chats(
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    user, _ = user_info
    return await ChatService.get_user_chats(db, user.id, skip, limit)

@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def read_chat(
    chat_id: str,
    user_info: Tuple[User, bool] = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    try:
        return await ChatService.add_message_to_chat(db, chat_id, message)
    except ValueError:
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while adding the message: {str(e)}")
    
@router.get("/me", response_model=UserInDB)
async def read_users_me(user_info: Tuple[UserInDB, bool] = Depends(get_current_user)):
    user, _ = user_info
    return user

@router.get("/user/{uid}", response_model=UserInDB)
async def read_user(uid: str, user_info: Tuple[User, bool] = Depends(get_current_user), db: Session = Depends(get_db)):
    user = await UserService.get_user_by_uid(db, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

