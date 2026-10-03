from fastapi import FastAPI

from app.api.v1.api import api_router
from app.config import settings
from app.core.logger import setup_logging

setup_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Advanced Stock Analysis Engine Toolkit",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
