"""Read-only Yahoo Finance MCP server powered by yfinance.

This server exposes freshly fetched public Yahoo Finance data to MCP clients.
Yahoo Finance data can be delayed, entitlement-dependent, rate-limited, or incomplete;
every response includes a fetched_at timestamp and source metadata.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import re
from datetime import date, datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

SERVER_NAME = "ASET Yahoo Finance"
MAX_HISTORY_ROWS = 2000
MAX_TABLE_ROWS = 250
MAX_COMPARE_SYMBOLS = 10
DEFAULT_TIMEOUT = float(os.getenv("YFINANCE_MCP_TIMEOUT_SECONDS", "30"))

mcp = MCPServer(
    SERVER_NAME,
    instructions=(
        "Read-only public market-data tools powered by the Python yfinance library "
        "against Yahoo Finance. Prefer get_quote for the latest available quote, "
        "get_history for price history, get_info for company/valuation metadata, "
        "and get_financials for income statement, balance sheet or cash flow data. "
        "Always report fetched_at and note that Yahoo Finance data may be delayed or "
        "subject to exchange/provider entitlements. Never invent missing values. "
        "This server does not place trades or provide personalized investment advice."
    ),
)


def _symbol(raw: str) -> str:
    value = str(raw).strip().upper()
    if not re.fullmatch(r"[A-Z0-9.^_=-]{1,20}", value):
        raise ToolError("Invalid Yahoo Finance symbol.")
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


def _frame_records(frame: pd.DataFrame | None, limit: int = MAX_TABLE_ROWS) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    working = frame.copy().reset_index()
    if len(working) > limit:
        working = working.tail(limit)
    import json

    return json.loads(working.to_json(orient="records", date_format="iso"))


def _series_records(series: pd.Series | None, limit: int = MAX_TABLE_ROWS) -> list[dict[str, Any]]:
    if series is None or series.empty:
        return []
    working = series.copy()
    if len(working) > limit:
        working = working.tail(limit)
    frame = working.rename("value").reset_index()
    import json

    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _quote_payload(symbol: str, fast_info: Any, info: dict[str, Any] | None) -> dict[str, Any]:
    info = info or {}
    keys = (
        "shortName",
        "longName",
        "quoteType",
        "currency",
        "exchange",
        "market",
        "fullExchangeName",
        "financialCurrency",
        "marketCap",
        "enterpriseValue",
        "trailingPE",
        "forwardPE",
        "priceToBook",
        "enterpriseToEbitda",
        "dividendYield",
        "profitMargins",
        "operatingMargins",
        "returnOnEquity",
        "returnOnAssets",
        "revenueGrowth",
        "earningsGrowth",
        "beta",
        "fiftyTwoWeekHigh",
        "fiftyTwoWeekLow",
        "sharesOutstanding",
    )
    selected = {key: info.get(key) for key in keys if key in info}
    fast = {}
    for key in (
        "currency",
        "exchange",
        "timezone",
        "last_price",
        "previous_close",
        "open",
        "day_high",
        "day_low",
        "year_high",
        "year_low",
        "year_change",
        "market_cap",
        "shares",
    ):
        try:
            fast[key] = fast_info[key]
        except Exception:
            continue
    return {
        "symbol": symbol,
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "data_disclaimer": "Latest available Yahoo Finance data; may be delayed and is not guaranteed real-time.",
        "fast_info": _jsonable(fast),
        "info": _jsonable(selected),
    }


async def _ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(_symbol(symbol))


@mcp.tool(
    title="Yahoo quote",
    description=(
        "Fetch the latest available Yahoo Finance quote snapshot for one ticker. "
        "Returns current/previous price, range, market cap and key valuation/profitability fields."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_quote(symbol: str) -> dict[str, Any]:
    ticker = await _ticker(symbol)
    fast = await asyncio.to_thread(ticker.get_fast_info)
    info = await asyncio.to_thread(ticker.get_info)
    return _quote_payload(_symbol(symbol), fast, info)


@mcp.tool(
    title="Yahoo price history",
    description=(
        "Fetch historical OHLCV data from Yahoo Finance through yfinance. "
        "Supports common Yahoo periods (1d to max) and intervals (1m to 3mo), "
        "with bounded output."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_history(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    start: str = "",
    end: str = "",
    auto_adjust: bool = False,
    prepost: bool = False,
) -> dict[str, Any]:
    allowed_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
    allowed_intervals = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}
    if not start and period not in allowed_periods:
        raise ToolError(f"period must be one of {sorted(allowed_periods)}")
    if interval not in allowed_intervals:
        raise ToolError(f"interval must be one of {sorted(allowed_intervals)}")
    if start and end and start > end:
        raise ToolError("start must not be after end.")
    ticker = await _ticker(symbol)

    def fetch() -> pd.DataFrame:
        kwargs: dict[str, Any] = {
            "interval": interval,
            "auto_adjust": auto_adjust,
            "prepost": prepost,
            "actions": True,
        }
        if start:
            kwargs["start"] = start
            if end:
                kwargs["end"] = end
        else:
            kwargs["period"] = period
        return ticker.history(**kwargs)

    frame = await asyncio.to_thread(fetch)
    records = _frame_records(frame, MAX_HISTORY_ROWS)
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "period": period if not start else None,
        "start": start or None,
        "end": end or None,
        "interval": interval,
        "auto_adjust": auto_adjust,
        "prepost": prepost,
        "rows_returned": len(records),
        "rows_truncated": bool(frame is not None and len(frame) > MAX_HISTORY_ROWS),
        "data": records,
    }


@mcp.tool(
    title="Yahoo company information",
    description=(
        "Fetch company identity, market classification, valuation, profitability, growth, "
        "risk and trading metadata from Yahoo Finance."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_info(symbol: str) -> dict[str, Any]:
    ticker = await _ticker(symbol)
    info = await asyncio.to_thread(ticker.get_info)
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "field_count": len(info),
        "data": _jsonable(info),
    }


@mcp.tool(
    title="Yahoo financial statements",
    description=(
        "Fetch annual or quarterly income statement, balance sheet, or cash flow statement "
        "from Yahoo Finance through yfinance."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_financials(
    symbol: str,
    statement: str = "income",
    frequency: str = "yearly",
    max_rows: int = 100,
) -> dict[str, Any]:
    if statement not in {"income", "balance_sheet", "cash_flow"}:
        raise ToolError("statement must be income, balance_sheet, or cash_flow.")
    if frequency not in {"yearly", "quarterly"}:
        raise ToolError("frequency must be yearly or quarterly.")
    max_rows = max(1, min(int(max_rows), MAX_TABLE_ROWS))
    ticker = await _ticker(symbol)

    def fetch() -> pd.DataFrame:
        if statement == "income":
            return ticker.get_income_stmt(as_dict=False, pretty=False, freq=frequency)
        if statement == "balance_sheet":
            return ticker.get_balance_sheet(as_dict=False, pretty=False, freq=frequency)
        return ticker.get_cash_flow(as_dict=False, pretty=False, freq=frequency)

    frame = await asyncio.to_thread(fetch)
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "statement": statement,
        "frequency": frequency,
        "rows_returned": min(len(frame.index), max_rows) if frame is not None else 0,
        "columns": [str(column) for column in frame.columns] if frame is not None else [],
        "data": _frame_records(frame, max_rows),
    }


@mcp.tool(
    title="Yahoo analyst and valuation data",
    description=(
        "Fetch analyst price targets, recommendations, earnings/revenue estimates, "
        "EPS trends and valuation measures from Yahoo Finance."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_analysis(symbol: str) -> dict[str, Any]:
    ticker = await _ticker(symbol)
    targets, recommendations, earnings_estimate, revenue_estimate, valuation = await asyncio.gather(
        asyncio.to_thread(ticker.get_analyst_price_targets),
        asyncio.to_thread(ticker.get_recommendations),
        asyncio.to_thread(ticker.get_earnings_estimate),
        asyncio.to_thread(ticker.get_revenue_estimate),
        asyncio.to_thread(lambda: ticker.get_valuation_measures(freq="quarterly", periods=5)),
    )
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "analyst_price_targets": _jsonable(targets),
        "recommendations": _frame_records(recommendations),
        "earnings_estimate": _frame_records(earnings_estimate),
        "revenue_estimate": _frame_records(revenue_estimate),
        "valuation_measures": _frame_records(valuation),
    }


@mcp.tool(
    title="Yahoo corporate actions",
    description="Fetch dividends, splits and combined corporate actions from Yahoo Finance.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_actions(symbol: str, period: str = "max") -> dict[str, Any]:
    if period not in {"1y", "2y", "5y", "10y", "max"}:
        raise ToolError("period must be one of 1y, 2y, 5y, 10y, max.")
    ticker = await _ticker(symbol)
    actions, dividends, splits = await asyncio.gather(
        asyncio.to_thread(lambda: ticker.get_actions(period=period)),
        asyncio.to_thread(lambda: ticker.get_dividends(period=period)),
        asyncio.to_thread(lambda: ticker.get_splits(period=period)),
    )
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "period": period,
        "actions": _series_records(actions),
        "dividends": _series_records(dividends),
        "splits": _series_records(splits),
    }


@mcp.tool(
    title="Yahoo options chain",
    description="Fetch available option expirations and an options chain for one Yahoo ticker.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_options(symbol: str, expiration: str = "", max_rows: int = 100) -> dict[str, Any]:
    max_rows = max(1, min(int(max_rows), MAX_TABLE_ROWS))
    ticker = await _ticker(symbol)
    expirations = await asyncio.to_thread(lambda: list(ticker.options))
    if not expirations:
        return {
            "symbol": _symbol(symbol),
            "provider": "Yahoo Finance via yfinance",
            "fetched_at": _now(),
            "expirations": [],
            "expiration_used": None,
            "calls": [],
            "puts": [],
        }
    chosen = expiration or expirations[0]
    if chosen not in expirations:
        raise ToolError(f"expiration must be one of the available expirations: {expirations[:30]}")
    chain = await asyncio.to_thread(lambda: ticker.option_chain(chosen))
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "expirations": expirations,
        "expiration_used": chosen,
        "calls": _frame_records(chain.calls, max_rows),
        "puts": _frame_records(chain.puts, max_rows),
    }


@mcp.tool(
    title="Yahoo stock search",
    description="Search Yahoo Finance for tickers and recent market/news results by company name or keyword.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def search_yahoo(query: str, max_results: int = 10, news_count: int = 5) -> dict[str, Any]:
    query = str(query).strip()
    if not query or len(query) > 100:
        raise ToolError("query must be 1-100 characters.")
    max_results = max(1, min(int(max_results), 25))
    news_count = max(0, min(int(news_count), 20))
    result = await asyncio.to_thread(
        lambda: yf.Search(
            query,
            max_results=max_results,
            news_count=news_count,
            include_cb=False,
            include_research=False,
        )
    )
    return {
        "query": query,
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "quotes": _jsonable(result.quotes),
        "news": _jsonable(result.news),
    }


@mcp.tool(
    title="Yahoo news",
    description="Fetch recent Yahoo Finance news for a ticker.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_news(symbol: str, count: int = 10) -> dict[str, Any]:
    count = max(1, min(int(count), 25))
    ticker = await _ticker(symbol)
    news = await asyncio.to_thread(lambda: ticker.get_news(count=count))
    return {
        "symbol": _symbol(symbol),
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "count": len(news),
        "news": _jsonable(news),
    }


@mcp.tool(
    title="Compare Yahoo quotes",
    description="Fetch and compare key quote and valuation fields for up to 10 Yahoo Finance tickers.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def compare_quotes(symbols: list[str]) -> dict[str, Any]:
    clean = [_symbol(item) for item in symbols]
    if not clean or len(clean) > MAX_COMPARE_SYMBOLS:
        raise ToolError(f"Provide 1-{MAX_COMPARE_SYMBOLS} symbols.")
    results = await asyncio.gather(*(get_quote(item) for item in clean))
    return {
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": _now(),
        "symbols": clean,
        "quotes": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ASET Yahoo Finance MCP server")
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8101")))
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
        return

    mcp.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=2 * 1024 * 1024,
    )


if __name__ == "__main__":
    main()
