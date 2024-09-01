# app/core/security.py

from fastapi import Depends, HTTPException, Request, Response, WebSocket, status
from starlette.websockets import WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials
from sqlalchemy.ext.asyncio import AsyncSession
import firebase_admin
from typing import Optional, Tuple
import time
from llamasearch.api.core.config import settings
from llamasearch.api.services.user import UserService
from llamasearch.api.db.session import get_db
from llamasearch.api.schemas.user import User, UserCreate
from llamasearch.api.services.session import session_service
from llamasearch.logger import logger

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)
security = HTTPBearer(auto_error=False)

async def verify_token_and_get_user(token: str, db: AsyncSession) -> User:
    try:
        decoded_token = auth.verify_id_token(token)
        firebase_user = auth.get_user(decoded_token['uid'])
        user_data = UserCreate(
            firebase_uid=firebase_user.uid,
            email=firebase_user.email,
            display_name=firebase_user.display_name or ""
        )
        user = await UserService.create_or_get_user(db, user_data)
        return user
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def create_session(user: User, db: AsyncSession) -> str:
    return await session_service.create_session(db, user.id)

async def get_current_user(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    logger.debug(f"Checking authentication for request to {request.url}")
    # Check for session-based authentication
    if hasattr(request.state, 'user') and request.state.user is not None:
        logger.debug(f"User authenticated via session: {request.state.user.email}")
        return request.state.user

    # Check for session cookie
    session_id = request.cookies.get("session_id")
    logger.debug(f"Session ID from cookie: {session_id}")
    if settings.USE_SESSION_AUTH and session_id:
        user = await session_service.validate_session(db, session_id)
        if user:
            logger.debug(f"User authenticated via session: {user.email}")
            return user

    # Check for bearer token
    auth_header = request.headers.get('Authorization')
    logger.debug(f"Authorization header: {auth_header}")
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user = await verify_token_and_get_user(token, db)
        logger.debug(f"User authenticated via token: {user.email}")
        return user

    logger.debug("No valid authentication found")
    raise HTTPException(status_code=401, detail="Authentication required")

# async def get_current_user_ws(
#     websocket: WebSocket,
#     db: AsyncSession = Depends(get_db),
#     token: str = None
# ) -> User:
#     if not token or not token.startswith('Bearer '):
#         raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)
#     token = token.split(' ')[1]
#     user = await verify_token_and_get_user(token, db)
#     if settings.USE_SESSION_AUTH:
#         session_id = await create_session(user, db)
#         print("Session id : {}".format(session_id))
#         websocket.cookies["session_id"] = session_id
#     return user

async def get_current_user_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    token: str = None
) -> Tuple[User, str]:
    # Check for session cookie
    session_id = websocket.cookies.get("session_id")
    if settings.USE_SESSION_AUTH and session_id:
        logger.info("WS AUTH ::Session validation for the websocket")
        user = await session_service.validate_session(db, session_id)
        if user:
            logger.info(f"WS AUTH ::User {user.email} authenticated via session {session_id}")
            return user, session_id

    # Check for bearer token
    if not token or not token.startswith('Bearer '):
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)
    token = token.split(' ')[1]
    user = await verify_token_and_get_user(token, db)
    logger.info(f"WS AUTH :: User authenticated via token: {user.email}")
    if settings.USE_SESSION_AUTH:
        session_id = await session_service.create_session(db, user.id)
    return user, session_id

def verify_and_refresh_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        # Check if token is close to expiration (e.g., within 5 minutes)
        if decoded_token['exp'] - time.time() < 300:
            # Token is about to expire, refresh it
            new_token = auth.create_custom_token(decoded_token['uid'])
            return new_token
        return token
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="Token revoked")

async def get_optional_user(
    request: Request,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[Tuple[User, bool]]:
    try:
        return await get_current_user(request, response, credentials, db)
    except HTTPException:
        return None, False

async def logout_user(
    request: Request,
    response: Response,
    user: Optional[User],
    db: AsyncSession = Depends(get_db)
) -> None:
    try:
        session_id = request.cookies.get("session_id")
        logger.info(f"Logout user with session {session_id}")
        if settings.USE_SESSION_AUTH and session_id:
            await session_service.end_session(db, session_id)
            logger.debug(f"Session ended for session_id: {session_id}")
        if user:
            try:
                logger.debug(f"Revoking refresh tokens for firebase user {user.firebase_uid}")
                auth.revoke_refresh_tokens(user.firebase_uid)
                logger.debug(f"Refresh tokens revoked for user {user.id}")
                logger.info(f"User {user.id} logged out successfully")
            except Exception as e:
                logger.error(f"Error revoking refresh tokens for user {user.id}: {str(e)}")
            await session_service.end_all_sessions(db, user.id)
        response.delete_cookie(key="firebase_token", path="/", domain=None)
        response.delete_cookie(key="session_id", path="/", domain=None)
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
        raise