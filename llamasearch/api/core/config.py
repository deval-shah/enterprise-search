# app/core/config.py
from pydantic import BaseSettings, AnyHttpUrl
from typing import List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: str = "LlamaSearch"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8010"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]
    PROJECT_NAME: str = "LlamaSearch"
    
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_SESSION_AUTH: bool = True
    COOKIE_SECURE: bool = False  # Set to True in production for HTTPS

    FIREBASE_CREDENTIALS_PATH: str = "firebase.json"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
