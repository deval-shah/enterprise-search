import os
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    SERVER_NAME: str = Field(default="EnterpriseSearch", env="SERVER_NAME")
    SERVER_HOST: str = Field(default="http://localhost:8010", env="SERVER_HOST")
    PROJECT_NAME: str = Field(default="EnterpriseSearch", env="PROJECT_NAME")

    # Toggle Settings
    ENABLE_RATE_LIMIT: int = Field(default=False, env="RATE_LIMIT_ENABLED")

    # CORS Settings
    BACKEND_CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3001,http://localhost:3002", env="BACKEND_CORS_ORIGINS")

    # Database Settings
    DATABASE_URL: str = Field(default='sqlite+aiosqlite:///./test.db', env="DATABASE_URL")

    # Redis Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Authentication Settings
    ENABLE_AUTH: bool = Field(default=True, env="ENABLE_AUTH")
    COOKIE_SECURE: bool = Field(default=False, env="COOKIE_SECURE")

    # Firebase Settings
    FIREBASE_CREDENTIALS_PATH: str = Field(default="/app/keys/firebase.json", env="FIREBASE_CREDENTIALS_PATH")

    # Application Paths
    APP_BASE_PATH: str = Field(default=".", env="APP_BASE_PATH")
    CONFIG_PATH: str = Field(default="config/config.dev.yaml", env="CONFIG_PATH")
    DATA_PATH: str = Field(default="data/sample-docs/", env="DATA_PATH")
    LOG_DIR: str = Field(default="data/app/logs", env="LOG_DIR")

    # Limits
    FILE_SIZE_LIMIT: int = Field(default=10 * 1024 * 1024)
    MAX_FILES_PER_USER: int = Field(default=100)
    MAX_FILES_PER_CHAT: int = Field(default=10)
    MAX_FILES: int = Field(default=10)

    # Logging
    LOGLEVEL: str = Field(default="DEBUG", env="LOGLEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    @property
    def BACKEND_CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

# @lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
