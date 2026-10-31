from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Backend / Application
    APP_ENV: Literal["development", "test", "production"] = "development"
    DATABASE_URL: str = "postgresql+psycopg://app:CHANGE_ME@postgres:5432/subscriptions"
    REDIS_URL: str = "redis://redis:6379/0"
    SESSION_SECRET: str = "REPLACE_WITH_RANDOM_SECRET"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Storage
    OBJECT_STORAGE_ENDPOINT: str = "http://minio:9000"
    OBJECT_STORAGE_BUCKET: str = "documents"
    OBJECT_STORAGE_ACCESS_KEY: str = "CHANGE_ME"
    OBJECT_STORAGE_SECRET_KEY: str = "CHANGE_ME"

    # Email
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025

    # AI Configuration (Gemini)
    GEMINI_API_KEY: str = "SET_SERVER_SIDE_ONLY"
    GEMINI_MODEL: str = "SET_VERIFIED_FREE_TIER_FLASH_MODEL"
    AI_ENABLED: bool = True
    AI_MAX_REQUESTS_PER_USER_PER_DAY: int = 20
    AI_TIMEOUT_SECONDS: int = 15

    # PostgreSQL container credentials
    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "CHANGE_ME"
    POSTGRES_DB: str = "subscriptions"

    # MinIO container credentials
    MINIO_ROOT_USER: str = "CHANGE_ME"
    MINIO_ROOT_PASSWORD: str = "CHANGE_ME"

    # Frontend
    VITE_API_BASE_URL: str = "http://localhost:8000/api/v1"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


settings: Settings = get_settings()
