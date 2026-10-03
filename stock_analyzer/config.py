"""Environment-backed configuration for the ASET service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "ASET Research API"
    environment: str = "development"
    allowed_origins: tuple[str, ...] = ()
    max_price_points: int = 500

    @classmethod
    def from_env(cls) -> "Settings":
        raw_origins = os.getenv("ASET_ALLOWED_ORIGINS", "")
        max_points = int(os.getenv("ASET_MAX_PRICE_POINTS", "500"))
        if not 1 <= max_points <= 10_000:
            raise ValueError("ASET_MAX_PRICE_POINTS must be between 1 and 10000")
        origins = tuple(item.strip() for item in raw_origins.split(",") if item.strip())
        return cls(
            app_name=os.getenv("ASET_APP_NAME", cls.app_name),
            environment=os.getenv("ASET_ENVIRONMENT", cls.environment),
            allowed_origins=origins,
            max_price_points=max_points,
        )


def cli() -> None:
    """Run the local ASET API with Uvicorn."""
    import uvicorn

    uvicorn.run("stock_analyzer.api:app", host="127.0.0.1", port=8000, reload=False)
