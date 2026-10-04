"""Versioned read-only API for ASET research data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings
from .providers import MarketDataProvider, make_provider_from_env


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    trading_date: date
    close: Decimal = Field(ge=0)
    currency: str
    provider: str
    source: str
    quality: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str


def _error(code: str, message: str, request_id: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"detail": {"code": code, "message": message, "request_id": request_id}}
    )


def create_app(provider: MarketDataProvider | None = None, settings: Settings | None = None) -> FastAPI:
    provider = provider or make_provider_from_env()
    settings = settings or Settings.from_env()
    app = FastAPI(title=settings.app_name, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["x-request-id", "content-type"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        supplied = request.headers.get("x-request-id")
        try:
            request_id = str(UUID(supplied)) if supplied else str(uuid4())
        except (ValueError, AttributeError):
            request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        if settings.environment.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error("invalid_request", "request validation failed", request.state.request_id, 422)

    router = APIRouter(prefix="/api/v1")

    @router.get("/health", tags=["platform"])
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "aset-research-api", "environment": settings.environment}

    @router.get("/readiness", tags=["platform"])
    async def readiness() -> dict[str, str]:
        return {"status": "ready", "provider": provider.name}

    @router.get(
        "/securities/{symbol}/prices",
        response_model=list[PriceResponse],
        responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
        tags=["market-data"],
    )
    async def prices(symbol: str, request: Request, start: date, end: date, limit: int = 500) -> list[PriceResponse]:
        request_id = request.state.request_id
        if start > end:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_period", "message": "start must not be after end", "request_id": request_id},
            )
        if limit < 1 or limit > settings.max_price_points:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_limit",
                    "message": f"limit must be between 1 and {settings.max_price_points}",
                    "request_id": request_id,
                },
            )
        try:
            observations = provider.get_prices(symbol, start, end)
        except KeyError as exc:
            raise HTTPException(
                status_code=404, detail={"code": "security_not_found", "message": str(exc), "request_id": request_id}
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "provider_unavailable",
                    "message": "market data provider unavailable",
                    "request_id": request_id,
                },
            ) from exc
        return [
            PriceResponse(
                symbol=item.security.symbol,
                trading_date=item.trading_date,
                close=item.close,
                currency=item.security.currency,
                provider=item.provenance.provider,
                source=item.provenance.source,
                quality=item.provenance.quality.value,
            )
            for item in observations[:limit]
        ]

    app.include_router(router)
    return app


app = create_app()
