# app/core/middleware.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from llamasearch.api.services.session import session_service
from llamasearch.api.db.session import get_db
from llamasearch.api.core.config import settings
from llamasearch.logger import logger

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db = next(get_db())
        session_id = request.cookies.get("session_id")
        request.state.user = None
        request.state.session_id = None
        if settings.USE_SESSION_AUTH and session_id:
            logger.info(f"Validating session: {session_id}")
            user = await session_service.validate_session(db, session_id)
            if user:
                logger.debug(f"Valid session found for user: {user.id}")
                request.state.user = user
                request.state.session_id = session_id
            else:
                logger.debug(f"Invalid or expired session: {session_id}")
                request.state.invalid_session = True

        response = await call_next(request)

        if hasattr(request.state, 'new_session_id'):
            logger.debug(f"Setting new session cookie: {request.state.new_session_id}")
            response.set_cookie(
                key="session_id",
                value=request.state.new_session_id,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite='lax',
                max_age=3600  # Set to match the Redis expiry time
            )
        elif hasattr(request.state, 'invalid_session') and request.state.invalid_session:
            # Only clear the cookie after the request has been processed
            logger.debug(f"Clearing invalid session cookie: {session_id}")
            response.delete_cookie(key="session_id")
        return response

async def session_middleware(request: Request, call_next):
    middleware = SessionMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
