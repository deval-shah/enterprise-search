# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from llamasearch.api.core.middleware import SessionMiddleware
from llamasearch.api.routes import router as api_router
from llamasearch.api.core.config import settings
from llamasearch.api.db.session import init_db
from llamasearch.api.core.redis import get_redis
from llamasearch.api.services.session import session_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=True
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.USE_SESSION_AUTH:
    print("Session authentication enabled")
    app.add_middleware(SessionMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    init_db()
    if settings.USE_SESSION_AUTH:
        redis_client = get_redis()
        session_service.init_redis(redis_client)
        print("Session authentication initialized with Redis")

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)