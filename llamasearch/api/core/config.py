from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: str = "LlamaSearch"
    SERVER_HOST: str = "http://localhost:8010"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    PROJECT_NAME: str = "LlamaSearch"
    
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_SESSION_AUTH: bool = True
    COOKIE_SECURE: bool = False  # Set to True in production for HTTPS

    FIREBASE_CREDENTIALS_PATH: str = "firebase.json"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    @property
    def BACKEND_CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

settings = Settings()
