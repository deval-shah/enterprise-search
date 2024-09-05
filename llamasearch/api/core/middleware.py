# app/core/middleware.py

from fastapi import Request, Response, HTTPException, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from llamasearch.api.services.session import session_service
from llamasearch.api.db.session import get_db
from llamasearch.api.core.config import settings
from llamasearch.logger import logger
from llamasearch.api.core.security  import get_current_user_ws

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Processing request: {request.method} {request.url}")
        session_id = request.cookies.get("session_id")
        logger.debug(f"Session ID from cookie: {session_id}")
        request.state.user = None
        request.state.session_id = None
        if settings.USE_SESSION_AUTH and session_id:
            async for db in get_db():
                user = await session_service.validate_session(db, session_id)
                if user:
                    request.state.user = user
                    request.state.session_id = session_id
                    logger.debug(f"SessionMiddleware: User authenticated via session: {user.email}")
                else:
                    logger.debug("SessionMiddleware: Invalid session")
        else:
            logger.debug(f"No session ID or session auth not enabled. USE_SESSION_AUTH: {settings.USE_SESSION_AUTH}")

        response = await call_next(request)
        logger.info(f"Request processed: {response.status_code}")
        if response is None:
            return Response(status_code=500)

        if hasattr(request.state, 'new_session_id'):
            logger.debug(f"Setting new session cookie: {request.state.new_session_id}")
            response.set_cookie(
                key="session_id",
                value=request.state.new_session_id,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite='lax',
                max_age=3600
            )
        elif hasattr(request.state, 'invalid_session') and request.state.invalid_session:
            logger.debug(f"Clearing invalid session cookie: {session_id}")
            response.delete_cookie(key="session_id")

        logger.info(f"Request processed: {response.status_code}")
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip] = [t for t in self.requests[client_ip] if current_time - t < self.window_seconds]
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Too many requests")
        self.requests[client_ip].append(current_time)
        response = await call_next(request)

class FileSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = None):
        super().__init__(app)
        self.max_size = max_size if max_size is not None else settings.FILE_SIZE_LIMIT

    async def dispatch(self, request: Request, call_next):
        # Check if the content length exceeds the max size
        if request.headers.get("content-length"):
            content_length = int(request.headers.get("content-length"))
            if content_length > self.max_size:
                return PlainTextResponse("File too large", status_code=413)
        
        response = await call_next(request)
        return response
    
async def session_middleware(request: Request, call_next):
    middleware = SessionMiddleware(app=None)
    return await middleware.dispatch(request, call_next)

async def filesize_middleware(request: Request, call_next):
    middleware = FileSizeLimitMiddleware(app=None)
    return await middleware.dispatch(request, call_next)