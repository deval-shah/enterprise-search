# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn
from llamasearch.api.core.middleware import SessionMiddleware
from llamasearch.api.routes import router
from llamasearch.api.core.config import settings
from llamasearch.api.db.session import init_db
from llamasearch.api.core.redis import get_redis
from llamasearch.api.services.session import session_service
from llamasearch.api.core.container import Container
from llamasearch.logger import logger

container = Container()
container.wire(modules=[".routes"])

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # debug=True,
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

app.include_router(router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    init_db()
    if settings.USE_SESSION_AUTH:
        redis_client = get_redis()
        session_service.init_redis(redis_client)
        print("Session authentication initialized with Redis")
    pipeline_factory = container.pipeline_factory()
    pipeline_factory.is_api_server = True
    await pipeline_factory.initialize_common_resources()
    logger.info("Pipeline factory initialized")

@app.on_event("shutdown")
async def shutdown_event():
    await container.pipeline_factory().cleanup_all()
    logger.info("Pipeline factory resources cleaned up")

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
    errors = exc.errors()
    body = exc.body
    if request.headers.get('content-type', '').startswith('multipart/form-data'):
        body = "Multipart form data (contents not shown for privacy reasons)"
    print(f"Validation error: {errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": str(body)},
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)