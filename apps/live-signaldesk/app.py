from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from source_reconciliation import reconcile_many

BASE_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "").strip()
TIMEOUT = float(os.getenv("ALPHAVANTAGE_TIMEOUT_SECONDS", "15"))
CACHE_TTL = int(os.getenv("SIGNALDESK_CACHE_TTL_SECONDS", "60"))
SYMBOL_RE = re.compile(r"^[A-Z0-9.:-]{1,15}$")
DEMO_SYMBOL = "IBM"
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="ASET SignalDesk Live", version="1.0.0")
CORS_ORIGINS = [
    item.strip() for item in os.getenv(
        "SIGNALDESK_CORS_ORIGINS",
        "http://tauri.localhost,http://localhost:1420,http://127.0.0.1:1420",
    ).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
cache: dict[str, tuple[float, dict[str, Any]]] = {}
lock = asyncio.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def number(value: Any) -> float | None:
    if value in (None, "", "None", "null", "N/A", "NaN", "-"):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def annual(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("annualReports")
    return rows if isinstance(rows, list) else []


def latest(payload: dict[str, Any], *fields: str) -> float | None:
    for row in annual(payload):
        for field in fields:
            value = number(row.get(field))
            if value is not None:
                return value
    return None


def provider_error(payload: dict[str, Any]) -> str | None:
    for key in ("Error Message", "Information", "Note"):
        if payload.get(key):
            return str(payload[key])
    return None


def freshness(entitlement: str | None) -> str:
    if entitlement == "realtime":
        return "Realtime entitlement"
    if entitlement == "delayed":
        return "15-minute delayed entitlement"
    return "Default quote freshness / provider-dependent"


async def av(
    function: str,
    symbol: str,
    entitlement: str | None = None,
    demo_allowed: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    demo = not API_KEY and demo_allowed and symbol == DEMO_SYMBOL
    if not API_KEY and not demo:
        raise HTTPException(
            status_code=503,
            detail="ALPHAVANTAGE_API_KEY is not configured. Add it to the server environment. Only IBM is available through the labeled demo preview.",
        )

    key = "demo" if demo else API_KEY
    params = {"function": function, "symbol": symbol, "apikey": key}
    if entitlement:
        params["entitlement"] = entitlement

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Alpha Vantage network error: {exc}") from exc

    error = provider_error(payload)
    if error:
        raise HTTPException(status_code=502, detail=f"Alpha Vantage: {error}")

    return payload, {
        "provider": "Alpha Vantage",
        "function": function,
        "fetched_at": now(),
        "mode": "demo-preview" if demo else "api-key",
        "freshness": freshness(entitlement),
    }


async def build_research(symbol: str, entitlement: str | None) -> dict[str, Any]:
    cache_key = f"{symbol}:{entitlement or 'default'}"
    async with lock:
        hit = cache.get(cache_key)
        if hit and time.time() - hit[0] < CACHE_TTL:
            result = dict(hit[1])
            result["meta"] = dict(result["meta"], cache="hit")
            return result

    quote, overview, income, balance = await asyncio.gather(
        av("GLOBAL_QUOTE", symbol, entitlement, True),
        av("OVERVIEW", symbol, None, True),
        av("INCOME_STATEMENT", symbol, None, True),
        av("BALANCE_SHEET", symbol, None, True),
    )

    q, qm = quote
    o, om = overview
    inc, im = income
    bal, bm = balance

    qd = q.get("Global Quote", {})
    price = number(qd.get("05. price"))
    change = number(qd.get("09. change"))
    change_pct = number(str(qd.get("10. change percent", "")).replace("%", ""))
    if change_pct is not None:
        change_pct /= 100

    history = [
        {
            "fiscal_date": row.get("fiscalDateEnding"),
            "revenue": number(row.get("totalRevenue")),
            "net_income": number(row.get("netIncome")),
        }
        for row in annual(inc)
    ]
    history = [row for row in history if row["fiscal_date"]][:5]

    balance_history = []
    for row in annual(bal)[:5]:
        balance_history.append(
            {
                "fiscal_date": row.get("fiscalDateEnding"),
                **{
                    key: number(value) if number(value) is not None else value
                    for key, value in row.items()
                    if key != "fiscalDateEnding"
                },
            }
        )

    cash_flow_raw = await av("CASH_FLOW", symbol, None, True)
    cash_flow_payload, cash_flow_meta = cash_flow_raw
    cash_flow_history = []
    for row in annual(cash_flow_payload)[:5]:
        cash_flow_history.append(
            {
                "fiscal_date": row.get("fiscalDateEnding"),
                **{
                    key: number(value) if number(value) is not None else value
                    for key, value in row.items()
                    if key != "fiscalDateEnding"
                },
            }
        )
    income_rows = [row for row in history if row["net_income"] is not None]
    latest_income = income_rows[0]["net_income"] if income_rows else None
    prior_income = income_rows[1]["net_income"] if len(income_rows) > 1 else None
    income_growth = (
        latest_income / prior_income - 1
        if latest_income is not None and prior_income not in (None, 0)
        else None
    )
    average_income = (
        sum(row["net_income"] for row in income_rows) / len(income_rows)
        if income_rows
        else None
    )

    revenue = latest(inc, "totalRevenue")
    debt = None
    balance_rows = annual(bal)
    if balance_rows:
        row = balance_rows[0]
        short_term = number(row.get("shortTermDebt")) or number(row.get("currentDebt")) or 0
        long_term = number(row.get("longTermDebt")) or number(row.get("longTermDebtNoncurrent")) or 0
        combined = short_term + long_term
        debt = combined if combined != 0 else latest(bal, "shortLongTermDebtTotal")
    cash = latest(
        bal,
        "cashAndCashEquivalentsAtCarryingValue",
        "cashAndShortTermInvestments",
    )
    market_cap = number(o.get("MarketCapitalization"))
    margin = (
        latest_income / revenue
        if latest_income is not None and revenue not in (None, 0)
        else None
    )
    debt_cash = debt / cash if debt is not None and cash not in (None, 0) else None
    cap_income = (
        market_cap / latest_income
        if market_cap is not None and latest_income not in (None, 0)
        else None
    )

    flags: list[str] = []
    if latest_income is None:
        flags.append("latest annual net income unavailable")
    if revenue is None:
        flags.append("latest annual revenue unavailable")
    if latest_income is not None and latest_income < 0:
        flags.append("latest annual net income is negative")
    if margin is not None and margin < 0:
        flags.append("negative net margin")
    if debt_cash is not None and debt_cash > 3:
        flags.append("debt/cash above 3x")
    if income_growth is not None and income_growth < 0:
        flags.append("latest annual net income declined vs prior year")

    result = {
        "symbol": symbol,
        "company": o.get("Name") or symbol,
        "exchange": o.get("Exchange"),
        "country": o.get("Country"),
        "currency": o.get("Currency"),
        "sector": o.get("Sector"),
        "industry": o.get("Industry"),
        "quote": {
            "price": price,
            "change": change,
            "change_percent": change_pct,
            "volume": number(qd.get("06. volume")),
        },
        "fundamentals": {
            "revenue": revenue,
            "net_income": latest_income,
            "net_margin": margin,
            "income_growth": income_growth,
            "average_5y_net_income": average_income,
            "debt": debt,
            "cash": cash,
            "debt_cash": debt_cash,
            "market_cap": market_cap,
            "market_cap_to_income": cap_income,
            "pe_ratio": number(o.get("PERatio")),
            "eps": number(o.get("EPS")),
            "operating_cash_flow": latest(cash_flow_payload, "operatingCashflow", "cashflowFromContinuingOperatingActivities"),
            "capital_expenditures": latest(cash_flow_payload, "capitalExpenditures"),
            "free_cash_flow": latest(cash_flow_payload, "freeCashFlow"),
        },
        "income_history": history,
        "balance_sheet_history": balance_history,
        "cash_flow_history": cash_flow_history,
        "flags": flags,
        "sources": [qm, om, im, bm, cash_flow_meta],
        "meta": {
            "provider": "Alpha Vantage",
            "fetched_at": now(),
            "freshness": freshness(entitlement),
            "cache": "miss",
            "demo_preview": any(x["mode"] == "demo-preview" for x in [qm, om, im, bm, cash_flow_meta]),
        },
    }

    async with lock:
        cache[cache_key] = (time.time(), result)
    return result


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "provider": "Alpha Vantage", "time": now()}


@app.get("/api/v1/research/{symbol}/verification")
async def research_verification(
    symbol: str,
    entitlement: str | None = Query(default=None, pattern="^(realtime|delayed)?$"),
) -> dict[str, Any]:
    """Cross-check ASET/Alpha Vantage research data against Yahoo Finance."""
    normalized = symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid ticker symbol.")
    primary = await build_research(normalized, entitlement)
    checks = await reconcile_many([primary], concurrency=1)
    return checks[0] if checks else {
        "symbol": normalized,
        "verification": {"status": "secondary_unavailable", "grade": "C"},
        "field_checks": {},
    }


@app.get("/api/v1/config")
async def config() -> dict[str, Any]:
    return {
        "provider": "Alpha Vantage",
        "api_key_configured": bool(API_KEY),
        "demo_preview_symbol": None if API_KEY else DEMO_SYMBOL,
        "cache_ttl_seconds": CACHE_TTL,
    }


@app.get("/api/v1/research/{symbol}")
async def research(
    symbol: str,
    entitlement: str | None = Query(default=None, pattern="^(realtime|delayed)?$"),
) -> dict[str, Any]:
    normalized = symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid ticker symbol.")
    return await build_research(normalized, entitlement)
