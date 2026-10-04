"""Environment-backed configuration for the ASET service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "ASET Research API"
    environment: str = "development"
    provider: str = "fixture"
    allowed_origins: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "testserver")
    max_price_points: int = 500
    yfinance_timeout_seconds: float = 8.0

    @classmethod
    def from_env(cls) -> "Settings":
        raw_origins = os.getenv("ASET_ALLOWED_ORIGINS", "")
        max_points = int(os.getenv("ASET_MAX_PRICE_POINTS", "500"))
        timeout = float(os.getenv("YFINANCE_TIMEOUT_SECONDS", "8"))
        if not 1 <= max_points <= 10_000:
            raise ValueError("ASET_MAX_PRICE_POINTS must be between 1 and 10000")
        if not 1 <= timeout <= 60:
            raise ValueError("YFINANCE_TIMEOUT_SECONDS must be between 1 and 60")
        origins = tuple(item.strip() for item in raw_origins.split(",") if item.strip())
        raw_hosts = os.getenv("ASET_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")
        hosts = tuple(item.strip() for item in raw_hosts.split(",") if item.strip())
        provider = os.getenv("ASET_PROVIDER", "fixture").strip().lower() or "fixture"
        return cls(
            app_name=os.getenv("ASET_APP_NAME", cls.app_name),
            environment=os.getenv("ASET_ENVIRONMENT", cls.environment),
            provider=provider,
            allowed_origins=origins,
            allowed_hosts=hosts,
            max_price_points=max_points,
            yfinance_timeout_seconds=timeout,
        )


def cli() -> None:
    """Run the local ASET API with Uvicorn."""
    import uvicorn

    uvicorn.run(
        "stock_analyzer.api:app",
        host=os.getenv("ASET_BIND_HOST", "127.0.0.1"),
        port=int(os.getenv("ASET_BIND_PORT", "8000")),
        reload=False,
    )
