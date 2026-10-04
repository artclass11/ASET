"""Concrete, lazy-loaded integrations for ASET's routed data sources.

The adapters import third-party projects only when selected by the router. This keeps
the core fast and avoids forcing every provider onto every installation.
"""

from __future__ import annotations

import importlib
import importlib.util
import shutil
import subprocess
from datetime import date, datetime, timezone
from typing import Any


class DataSourceUnavailable(RuntimeError):
    """Raised when a selected optional data project is not installed/configured."""


def _require(module: str, package: str | None = None) -> Any:
    if importlib.util.find_spec(module) is None:
        raise DataSourceUnavailable(
            f"{package or module} is not installed. Install the matching ASET optional extra."
        )
    return importlib.import_module(module)


def fetch_universe_financedatabase(
    *,
    country: str | None = None,
    exchange: str | None = None,
    sector: str | None = None,
    industry: str | None = None,
    min_market_cap: float | None = None,
    max_market_cap: float | None = None,
    only_primary_listing: bool = True,
    include_delisted: bool = False,
    limit: int = 10_000,
) -> dict[str, Any]:
    from .data_router import filter_finance_database

    return filter_finance_database(
        country=country,
        exchange=exchange,
        sector=sector,
        industry=industry,
        min_market_cap=min_market_cap,
        max_market_cap=max_market_cap,
        only_primary_listing=only_primary_listing,
        include_delisted=include_delisted,
        limit=limit,
    )


def fetch_yfinance_prices(
    symbols: list[str],
    *,
    start: date | None = None,
    end: date | None = None,
    period: str | None = "1y",
    auto_adjust: bool = False,
) -> dict[str, Any]:
    """Download many symbols in one yfinance request and normalize to records."""
    yf = _require("yfinance", "yfinance")
    if not symbols:
        raise ValueError("symbols must not be empty")
    clean = list(dict.fromkeys(str(x).strip().upper() for x in symbols if str(x).strip()))
    kwargs: dict[str, Any] = {
        "tickers": clean,
        "auto_adjust": auto_adjust,
        "progress": False,
        "threads": True,
    }
    if start is not None:
        kwargs["start"] = start.isoformat()
    if end is not None:
        kwargs["end"] = end.isoformat()
    elif period:
        kwargs["period"] = period

    frame = yf.download(**kwargs)
    if frame is None or frame.empty:
        return {
            "status": "empty",
            "provider": "yfinance",
            "record_count": 0,
            "symbols": clean,
            "records": [],
        }

    records: list[dict[str, Any]] = []
    columns = frame.columns
    multi = getattr(columns, "nlevels", 1) > 1

    for timestamp, row in frame.iterrows():
        trading_date = getattr(timestamp, "date", lambda: timestamp)()
        if multi:
            for symbol in clean:
                sub = None
                try:
                    sub = row.xs(symbol, level=-1)
                except (KeyError, IndexError):
                    try:
                        sub = row.xs(symbol, level=0)
                    except (KeyError, IndexError):
                        sub = None
                if sub is None:
                    continue
                close = sub.get("Close") if hasattr(sub, "get") else None
                if close is None:
                    continue
                records.append(
                    {
                        "symbol": symbol,
                        "trading_date": str(trading_date),
                        "open": _finite(sub.get("Open")),
                        "high": _finite(sub.get("High")),
                        "low": _finite(sub.get("Low")),
                        "close": _finite(close),
                        "volume": _finite(sub.get("Volume")),
                        "provider": "yfinance",
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        else:
            symbol = clean[0]
            records.append(
                {
                    "symbol": symbol,
                    "trading_date": str(trading_date),
                    "open": _finite(row.get("Open")),
                    "high": _finite(row.get("High")),
                    "low": _finite(row.get("Low")),
                    "close": _finite(row.get("Close")),
                    "volume": _finite(row.get("Volume")),
                    "provider": "yfinance",
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return {
        "status": "ok",
        "provider": "yfinance",
        "record_count": len(records),
        "symbols": clean,
        "records": records,
    }


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and number not in (float("inf"), float("-inf")) else None


def fetch_yfinance_fundamentals(symbol: str) -> dict[str, Any]:
    """Fetch one company's profile and annual statements; intended for shortlist depth."""
    yf = _require("yfinance", "yfinance")
    ticker = yf.Ticker(symbol.strip().upper())
    info = ticker.get_info()

    def records(frame: Any) -> list[dict[str, Any]]:
        if frame is None or getattr(frame, "empty", True):
            return []
        result = []
        for column in frame.columns:
            item = {"period": str(column)}
            for index in frame.index:
                item[str(index)] = _finite(frame.loc[index, column])
            result.append(item)
        return result

    financials = ticker.get_financials(freq="yearly")
    valuation = ticker.get_valuation_measures(freq="yearly", periods=5)
    return {
        "status": "ok",
        "provider": "yfinance",
        "symbol": symbol.strip().upper(),
        "profile": {
            "name": info.get("longName") or info.get("shortName"),
            "exchange": info.get("exchange"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": _finite(info.get("marketCap")),
        },
        "financials": records(financials),
        "valuation": records(valuation),
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_sec_company_filing(
    symbol: str,
    *,
    form: str = "10-K",
) -> dict[str, Any]:
    """Retrieve the latest SEC filing through EdgarTools."""
    edgar = _require("edgar", "edgartools")
    identity = __import__("os").getenv("EDGAR_IDENTITY", "").strip()
    if not identity:
        raise DataSourceUnavailable("EDGAR_IDENTITY is required for SEC/EdgarTools access.")
    edgar.set_identity(identity)
    company = edgar.Company(symbol.strip().upper())
    filing = company.get_filings(form=form).latest()
    return {
        "status": "ok",
        "provider": "EdgarTools",
        "symbol": symbol.strip().upper(),
        "form": form,
        "filing": {
            "accession": getattr(filing, "accession_number", None),
            "filing_date": str(getattr(filing, "filing_date", "")),
            "report_date": str(getattr(filing, "report_date", "")),
            "url": getattr(filing, "homepage_url", None),
        },
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_macro_series(
    symbols: str | list[str],
    *,
    start: date,
    end: date,
) -> dict[str, Any]:
    """Fetch maintained macro/statistical series through pandas-datareader."""
    pdr = _require("pandas_datareader", "pandas-datareader")
    names = [symbols] if isinstance(symbols, str) else list(symbols)
    if hasattr(pdr, "macro") and hasattr(pdr.macro, "read_macro"):
        result = pdr.macro.read_macro(names, start=start, end=end)
    else:
        result = {name: pdr.get_data_fred(name, start=start, end=end) for name in names}

    if hasattr(result, "to_dict"):
        payload = result.to_dict()
    else:
        payload = {
            name: frame.to_dict() if hasattr(frame, "to_dict") else frame
            for name, frame in result.items()
        }
    return {
        "status": "ok",
        "provider": "pandas-datareader",
        "symbols": names,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "data": payload,
    }


def source_engine_status() -> dict[str, Any]:
    """Return runtime status for data and quant projects without importing everything."""
    checks = {
        "yfinance": importlib.util.find_spec("yfinance") is not None,
        "financedatabase": importlib.util.find_spec("financedatabase") is not None,
        "akshare": importlib.util.find_spec("akshare") is not None,
        "edgartools": importlib.util.find_spec("edgar") is not None,
        "sec_edgar_downloader": importlib.util.find_spec("sec_edgar_downloader") is not None,
        "pandas_datareader": importlib.util.find_spec("pandas_datareader") is not None,
        "openbb": importlib.util.find_spec("openbb") is not None,
        "vectorbt": importlib.util.find_spec("vectorbt") is not None,
        "backtrader": importlib.util.find_spec("backtrader") is not None,
        "lean_cli": shutil.which("lean") is not None,
    }
    return checks


def choose_backtest_engine(prefer: str = "auto") -> dict[str, Any]:
    status = source_engine_status()
    if prefer != "auto":
        mapping = {
            "vectorbt": ("vectorbt", status["vectorbt"]),
            "backtrader": ("backtrader", status["backtrader"]),
            "lean": ("lean_cli", status["lean_cli"]),
        }
        if prefer not in mapping or not mapping[prefer][1]:
            return {"selected": None, "status": status, "reason": f"requested engine {prefer!r} is unavailable"}
        return {"selected": mapping[prefer][0], "status": status, "reason": "explicit preference"}

    if status["vectorbt"]:
        return {"selected": "vectorbt", "status": status, "reason": "fast matrix/vector workflow available"}
    if status["backtrader"]:
        return {"selected": "backtrader", "status": status, "reason": "event-driven engine available"}
    if status["lean_cli"]:
        return {"selected": "lean_cli", "status": status, "reason": "LEAN CLI available"}
    return {"selected": None, "status": status, "reason": "no quant engine installed"}


__all__ = [
    "DataSourceUnavailable",
    "choose_backtest_engine",
    "fetch_macro_series",
    "fetch_sec_company_filing",
    "fetch_universe_financedatabase",
    "fetch_yfinance_fundamentals",
    "fetch_yfinance_prices",
    "source_engine_status",
]
