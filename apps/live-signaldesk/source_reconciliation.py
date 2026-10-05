from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from typing import Any, Iterable

import yfinance as yf


FIELDS = ("revenue", "net_income", "market_cap", "debt", "cash")
DEFAULT_REL_TOLERANCE = 0.05
CLOSE_REL_TOLERANCE = 0.02


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _statement_value(frame: Any, rows: Iterable[str]) -> float | None:
    if frame is None or getattr(frame, "empty", True):
        return None
    for row in rows:
        try:
            series = frame.loc[row]
        except (KeyError, TypeError):
            continue
        for value in getattr(series, "tolist", lambda: [])():
            numeric = _number(value)
            if numeric is not None:
                return numeric
    return None


def _yahoo_snapshot(symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    try:
        info = ticker.get_info() or {}
    except Exception:
        info = {}
    try:
        income = ticker.get_income_stmt(as_dict=False, pretty=False, freq="yearly")
    except Exception:
        income = None
    try:
        balance = ticker.get_balance_sheet(as_dict=False, pretty=False, freq="yearly")
    except Exception:
        balance = None
    try:
        fast_info = ticker.fast_info
    except Exception:
        fast_info = None

    market_cap = _number(info.get("marketCap"))
    if market_cap is None and fast_info is not None:
        try:
            market_cap = _number(fast_info.get("market_cap"))
        except AttributeError:
            market_cap = _number(getattr(fast_info, "market_cap", None))

    return {
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "fields": {
            "revenue": _statement_value(income, ("Total Revenue", "Operating Revenue")),
            "net_income": _statement_value(
                income,
                ("Net Income", "Net Income Common Stockholders"),
            ),
            "market_cap": market_cap,
            "debt": _statement_value(
                balance,
                ("Total Debt", "Total Debt And Other Financing"),
            ),
            "cash": _statement_value(
                balance,
                (
                    "Cash Cash Equivalents And Short Term Investments",
                    "Cash And Cash Equivalents",
                    "Cash Financial",
                ),
            ),
        },
    }


def _compare(primary: Any, secondary: Any) -> dict[str, Any]:
    a = _number(primary)
    b = _number(secondary)
    if a is None or b is None:
        return {
            "status": "unavailable",
            "primary": a,
            "secondary": b,
            "relative_difference": None,
        }
    denominator = max(abs(a), abs(b), 1.0)
    difference = abs(a - b) / denominator
    if difference <= CLOSE_REL_TOLERANCE:
        status = "match"
    elif difference <= DEFAULT_REL_TOLERANCE:
        status = "close"
    else:
        status = "conflict"
    return {
        "status": status,
        "primary": a,
        "secondary": b,
        "relative_difference": round(difference, 6),
    }


def reconcile_rows(
    primary_rows: Iterable[dict[str, Any]],
    yahoo_snapshots: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in primary_rows:
        symbol = str(row.get("symbol") or "").upper()
        fundamentals = row.get("fundamentals") or {}
        yahoo = yahoo_snapshots.get(symbol)
        comparisons: dict[str, dict[str, Any]] = {}
        matched = 0
        conflicts = 0
        cross_checkable = 0

        if yahoo:
            secondary_fields = yahoo.get("fields") or {}
            for field in FIELDS:
                result = _compare(fundamentals.get(field), secondary_fields.get(field))
                comparisons[field] = result
                if result["status"] != "unavailable":
                    cross_checkable += 1
                if result["status"] == "match":
                    matched += 1
                elif result["status"] == "conflict":
                    conflicts += 1

        if not yahoo:
            overall_status = "single_source"
            verification_grade = "C"
        elif conflicts:
            overall_status = "conflict"
            verification_grade = "D"
        elif matched >= 3:
            overall_status = "cross_checked"
            verification_grade = "A"
        elif matched >= 1:
            overall_status = "partial_cross_check"
            verification_grade = "B"
        else:
            overall_status = "secondary_unavailable"
            verification_grade = "C"

        output.append(
            {
                "symbol": symbol,
                "company": row.get("company"),
                "verification": {
                    "status": overall_status,
                    "grade": verification_grade,
                    "primary_source": row.get("provider")
                    or row.get("source")
                    or (row.get("meta") or {}).get("provider")
                    or "ASET provider payload",
                    "secondary_source": yahoo.get("provider")
                    if yahoo
                    else "Yahoo Finance via yfinance",
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "matched_fields": matched,
                    "cross_checkable_fields": cross_checkable,
                    "conflict_fields": conflicts,
                    "primary_source_verification": "pending",
                    "material_claims_note": (
                        "Cross-provider agreement is not equivalent to primary filing verification."
                    ),
                },
                "field_checks": comparisons,
            }
        )
    return output


async def reconcile_many(
    primary_rows: Iterable[dict[str, Any]],
    *,
    concurrency: int = 4,
) -> list[dict[str, Any]]:
    rows = list(primary_rows)
    semaphore = asyncio.Semaphore(max(1, min(int(concurrency), 16)))
    snapshots: dict[str, dict[str, Any]] = {}

    async def worker(row: dict[str, Any]) -> None:
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            return
        async with semaphore:
            try:
                snapshots[symbol] = await asyncio.to_thread(_yahoo_snapshot, symbol)
            except Exception:
                return

    await asyncio.gather(*(worker(row) for row in rows))
    return reconcile_rows(rows, snapshots)
