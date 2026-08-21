from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Developer Intelligence API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://app:change-me-local-only@localhost:5432/developer_intelligence"
    api_cors_origins: list[AnyHttpUrl] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_upload_bytes: int = Field(default=1_048_576, ge=1, le=10_485_760)
    max_repository_files: int = Field(default=10_000, ge=1, le=100_000)
    max_repository_bytes: int = Field(default=104_857_600, ge=1, le=1_073_741_824)


@lru_cache
def get_settings() -> Settings:
    return Settings()
