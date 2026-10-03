"""Versioned read-only API for ASET research data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from .providers import MarketDataProvider, make_fixture_provider


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


def create_app(provider: MarketDataProvider | None = None) -> FastAPI:
    provider = provider or make_fixture_provider()
    app = FastAPI(title="ASET Research API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    router = APIRouter(prefix="/api/v1")

    @router.get("/health", tags=["platform"])
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "aset-research-api"}

    @router.get("/readiness", tags=["platform"])
    async def readiness() -> dict[str, str]:
        return {"status": "ready", "provider": provider.name}

    @router.get(
        "/securities/{symbol}/prices",
        response_model=list[PriceResponse],
        responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
        tags=["market-data"],
    )
    async def prices(symbol: str, request: Request, start: date, end: date) -> list[PriceResponse]:
        request_id = request.state.request_id
        if start > end:
            raise HTTPException(status_code=422, detail={"code": "invalid_period", "message": "start must not be after end", "request_id": request_id})
        try:
            observations = provider.get_prices(symbol, start, end)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "security_not_found", "message": str(exc), "request_id": request_id}) from exc
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
            for item in observations
        ]

    app.include_router(router)
    return app


app = create_app()
