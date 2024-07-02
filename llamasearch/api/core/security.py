# app/core/security.py

from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials
from sqlalchemy.orm import Session
import firebase_admin
from llamasearch.api.core.config import settings
from llamasearch.api.services.user import UserService
from llamasearch.api.db.session import get_db
from llamasearch.api.schemas.user import User, UserCreate
from llamasearch.api.services.session import session_service
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
    db: Session = Depends(get_db)
) -> Tuple[User, bool]:
    user = request.state.user
    is_new_session = False

    if user:
        print(f"User {user} already authenticated, new session : {is_new_session}")
        return user, is_new_session

    # If no valid session, authenticate with Firebase token
    if not credentials:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
        else:
            raise HTTPException(status_code=401, detail="Authentication credentials required")
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        firebase_user = auth.get_user(decoded_token['uid'])
        user_data = UserCreate(
            firebase_uid=firebase_user.uid,
            email=firebase_user.email,
            display_name=firebase_user.display_name or ""
        )
        user = await UserService.create_or_get_user(db, user_data)

        if settings.USE_SESSION_AUTH:
            session_id = request.state.session_id or request.cookies.get("session_id")
            if session_id:
                # Session validation is already done by middleware, so we can skip it here
                if not request.state.user:
                    # If middleware didn't set the user, we need to validate the session
                    user = await session_service.validate_session(db, session_id)
                    if user:
                        request.state.user = user
                        request.state.session_id = session_id
                        logger.info(f"Existing session validated: {session_id}")
                    else:
                        # If the session is invalid or expired, create a new one
                        session_id = await session_service.create_session(db, user.id)
                        request.state.new_session_id = session_id
                        is_new_session = True
                        logger.info(f"New session created: {session_id}")
            else:
                # If no session exists, create a new one
                session_id = await session_service.create_session(db, user.id)
                request.state.new_session_id = session_id
                is_new_session = True
                logger.info(f"New session created: {session_id}")

        return user, is_new_session
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {str(e)}")

async def get_optional_user(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Tuple[User, bool]]:
    try:
        return await get_current_user(request, response, credentials, db)
    except HTTPException:
        return None, False

async def logout_user(
    request: Request,
    response: Response,
    user: User,
    db: Session
) -> None:
    try:
        session_id = request.cookies.get("session_id")
        logger.info(f"Logout user with session {session_id}")

        # Handle session-based logout
        if settings.USE_SESSION_AUTH and session_id:
            await session_service.end_session(db, session_id)
            response.delete_cookie(key="session_id", path="/", domain=None)
            logger.info(f"Session ended for user {user.id}")

        # Handle token-based logout (Firebase)
        try:
            logger.info(f"Logout user for firebase user {user.firebase_uid}")
            auth.revoke_refresh_tokens(user.firebase_uid)
            logger.info(f"Refresh tokens revoked for user {user.id}")
        except Exception as e:
            logger.error(f"Error revoking refresh tokens for user {user.id}: {str(e)}")
        
        logger.info("Clearing cookies")
        # Clear any other client-side storage
        response.delete_cookie(key="firebase_token", path="/", domain=None)
        
        # Invalidate all sessions for this user
        await session_service.end_all_sessions(db, user.id)

    except Exception as e:
        logger.error(f"Unexpected error during logout for user {user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during logout")