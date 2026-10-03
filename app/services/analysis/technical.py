from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import yfinance as yf


class MarketDataFetcher:
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[datetime, Any]] = {}

    def get_quote(self, symbol: str, period: str = "1mo") -> dict[str, Any]:
        cache_key = f"quote:{symbol}:{period}"
        cached = self._cache.get(cache_key)
        now = datetime.utcnow()
        if cached and (now - cached[0]).total_seconds() < self.cache_ttl:
            return cached[1]

        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        if data.empty:
            raise ValueError(f"No data found for symbol: {symbol}")

        result = {
            "symbol": symbol,
            "current_price": float(data["Close"].iloc[-1]),
            "previous_close": float(data["Close"].iloc[-2]) if len(data) > 1 else None,
            "change_percent": float(((data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2]) * 100) if len(data) > 1 else 0.0,
            "history": data.reset_index().to_dict(orient="records"),
        }

        self._cache[cache_key] = (now, result)
        return result

    def get_historical(self, symbol: str, period: str = "1y", interval: str = "1d") -> dict[str, Any]:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        if history.empty:
            raise ValueError(f"No historical data found for symbol: {symbol}")
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "history": history.reset_index().to_dict(orient="records"),
        }

    def get_market_snapshot(self, symbols: list[str]) -> list[dict[str, Any]]:
        return [self.get_quote(symbol) for symbol in symbols]


market_data_fetcher = MarketDataFetcher()
