from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings(BaseSettings):
    app_name: str = "ASET"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    api_v1_str: str = "/api/v1"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    database_url: str = "sqlite:///./aset.db"
    database_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://localhost:8000",
    ]

    yfinance_cache_ttl: int = 3600
    polygon_api_key: str | None = None

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = get_settings()
