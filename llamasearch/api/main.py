# app/main.py
from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from dependency_injector.wiring import inject, Provide
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
from llamasearch.api.core.middleware import SessionMiddleware
from llamasearch.api.routes import router
from llamasearch.api.core.config import settings
from llamasearch.api.core.redis import get_redis
from llamasearch.api.services.session import session_service
from llamasearch.api.core.container import Container
from llamasearch.logger import logger
from llamasearch.api.db.session import init_db, close_db
from llamasearch.api.websocket_manager import websocket_manager
from llamasearch.api.core.security import get_current_user_ws
from llamasearch.api.db.session import get_db
from llamasearch.api.query_processor import process_query
from llamasearch.pipeline import PipelineFactory
from llamasearch.api.ws_routes import ws_router
from llamasearch.api.db.session import sessionmanager, Base
import logging

logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.WARNING)

container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    await init_db()
    if settings.USE_SESSION_AUTH:
        redis_client = get_redis()
        session_service.init_redis(redis_client)
        print(redis_client)
        print("Session authentication initialized with Redis")
    pipeline_factory = container.pipeline_factory()
    pipeline_factory.is_api_server = True
    await pipeline_factory.initialize_common_resources()
    logger.info("Pipeline factory initialized")
    logger.info("WebSocket manager initialized")

    yield
    # Cleanup
    await container.pipeline_factory().cleanup_all()
    logger.info("Pipeline factory resources cleaned up")
    for client_id in list(app.state.websocket_manager.active_connections.keys()):
        await app.state.websocket_manager.disconnect(client_id)
    logger.info("All WebSocket connections closed")
    await close_db()

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=False,
    dependencies=[Depends(container.wire)]
)

if settings.BACKEND_CORS_ORIGINS_LIST:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
if settings.USE_SESSION_AUTH:
    print("Session authentication enabled")
    app.add_middleware(SessionMiddleware)

# Initialize ConnectionManager
app.state.websocket_manager = websocket_manager

# Wire the container
container.wire(modules=[__name__, "llamasearch.api.routes", "llamasearch.api.ws_routes"])

# Include routers
app.include_router(router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {"message": "Welcome to LlamaSearch Backend service!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An unexpected error occurred: {str(exc)}"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.method == "OPTIONS":
        return JSONResponse(status_code=200)
    errors = exc.errors()
    body = exc.body
    if request.headers.get('content-type', '').startswith('multipart/form-data'):
        body = "Multipart form data (contents not shown for privacy reasons)"
    print(f"Validation error: {errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": str(body)},
    )

def get_websocket_manager():
    return app.state.websocket_manager

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)