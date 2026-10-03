from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.analysis.technical import analyze_series
from app.services.market_data.fetcher import market_data_fetcher

router = APIRouter()


@router.get("/{symbol}")
async def get_stock(symbol: str) -> dict:
    normalized = symbol.upper()
    try:
        quote = market_data_fetcher.get_quote(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"symbol": normalized, "data": quote}


@router.get("/{symbol}/historical")
async def get_stock_historical(
    symbol: str,
    period: str = Query(default="1y", description="Yahoo Finance period"),
    interval: str = Query(default="1d", description="Yahoo Finance interval"),
) -> dict:
    normalized = symbol.upper()
    try:
        result = market_data_fetcher.get_historical(normalized, period=period, interval=interval)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result


@router.get("/{symbol}/analysis/technical")
async def get_stock_technical_analysis(symbol: str) -> dict:
    normalized = symbol.upper()
    try:
        quote = market_data_fetcher.get_quote(normalized, period="6mo")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    closes = [row["Close"] for row in quote["history"] if "Close" in row]
    analysis = analyze_series(closes)
    return {"symbol": normalized, "technical": analysis}
