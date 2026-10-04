"""Concrete, lazy-loaded integrations for ASET's routed data sources.

Adapters are imported only when selected by the router. The core package remains
fast and lightweight while the optional projects remain independently usable.
"""

from __future__ import annotations

import concurrent.futures
import importlib
import importlib.util
import shutil
from datetime import date, datetime, timezone, timedelta
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
    market_cap_categories: list[str] | None = None,
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
        market_cap_categories=market_cap_categories,
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
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Download many symbols in one yfinance request and normalize to records."""
    yf = _require("yfinance", "yfinance")
    clean = list(dict.fromkeys(str(x).strip().upper() for x in symbols if str(x).strip()))
    if not clean:
        raise ValueError("symbols must not be empty")

    kwargs: dict[str, Any] = {
        "tickers": clean,
        "auto_adjust": auto_adjust,
        "progress": False,
        "threads": True,
        "timeout": timeout,
        "group_by": "column",
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
    multi = getattr(frame.columns, "nlevels", 1) > 1

    for timestamp, row in frame.iterrows():
        trading_date = timestamp.date() if hasattr(timestamp, "date") else date.fromisoformat(str(timestamp)[:10])

        if multi:
            ticker_level = frame.columns.names.index("Ticker") if "Ticker" in frame.columns.names else 1
            price_level = frame.columns.names.index("Price") if "Price" in frame.columns.names else 0
            available = set(frame.columns.get_level_values(ticker_level))
            for symbol in clean:
                if symbol not in available:
                    continue
                try:
                    sub = row.xs(symbol, level=ticker_level)
                except (KeyError, IndexError):
                    continue
                close = sub.get("Close")
                close_value = _finite(close)
                if close_value is None or close_value <= 0:
                    continue
                records.append(
                    {
                        "symbol": symbol,
                        "trading_date": str(trading_date),
                        "open": _finite(sub.get("Open")),
                        "high": _finite(sub.get("High")),
                        "low": _finite(sub.get("Low")),
                        "close": close_value,
                        "volume": _finite(sub.get("Volume")),
                        "provider": "yfinance",
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        else:
            symbol = clean[0]
            close_value = _finite(row.get("Close"))
            if close_value is None or close_value <= 0:
                continue
            records.append(
                {
                    "symbol": symbol,
                    "trading_date": str(trading_date),
                    "open": _finite(row.get("Open")),
                    "high": _finite(row.get("High")),
                    "low": _finite(row.get("Low")),
                    "close": close_value,
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


def _frame_records(frame: Any) -> list[dict[str, Any]]:
    if frame is None or getattr(frame, "empty", True):
        return []
    result: list[dict[str, Any]] = []
    for column in frame.columns:
        item = {"period": str(column)}
        for index in frame.index:
            item[str(index)] = _finite(frame.loc[index, column])
        result.append(item)
    return result


def fetch_yfinance_fundamentals(symbol: str) -> dict[str, Any]:
    """Fetch one company's profile, annual statements and valuation history."""
    yf = _require("yfinance", "yfinance")
    normalized = symbol.strip().upper()
    ticker = yf.Ticker(normalized)
    info = ticker.get_info()
    return {
        "status": "ok",
        "provider": "yfinance",
        "symbol": normalized,
        "profile": {
            "name": info.get("longName") or info.get("shortName"),
            "exchange": info.get("exchange"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": _finite(info.get("marketCap")),
            "enterprise_value": _finite(info.get("enterpriseValue")),
        },
        "income_statement": _frame_records(ticker.get_income_stmt(freq="yearly")),
        "balance_sheet": _frame_records(ticker.get_balance_sheet(freq="yearly")),
        "cash_flow": _frame_records(ticker.get_cash_flow(freq="yearly")),
        "valuation": _frame_records(ticker.get_valuation_measures(freq="yearly", periods=5)),
        "estimates": {
            "earnings": ticker.get_earnings_estimate(as_dict=True),
            "revenue": ticker.get_revenue_estimate(as_dict=True),
            "growth": ticker.get_growth_estimates(as_dict=True),
            "eps_trend": ticker.get_eps_trend(as_dict=True),
            "eps_revisions": ticker.get_eps_revisions(as_dict=True),
        },
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_yfinance_fundamentals_many(
    symbols: list[str],
    *,
    max_workers: int = 8,
) -> dict[str, Any]:
    """Enrich only a bounded shortlist in parallel."""
    clean = list(dict.fromkeys(str(x).strip().upper() for x in symbols if str(x).strip()))
    if not clean:
        raise ValueError("symbols must not be empty")
    workers = max(1, min(int(max_workers), 16))
    successes: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    def one(symbol: str) -> dict[str, Any]:
        return fetch_yfinance_fundamentals(symbol)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, symbol): symbol for symbol in clean}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                successes.append(future.result())
            except Exception as exc:
                failures.append({"symbol": symbol, "error": str(exc)})

    successes.sort(key=lambda item: item["symbol"])
    failures.sort(key=lambda item: item["symbol"])
    return {
        "status": "ok",
        "provider": "yfinance",
        "requested_symbols": len(clean),
        "succeeded_symbols": len(successes),
        "failed_symbols": len(failures),
        "results": successes,
        "failures": failures,
    }


def screen_yfinance_equities(
    *,
    region: str | None = None,
    sectors: list[str] | None = None,
    exchanges: list[str] | None = None,
    min_market_cap: float | None = None,
    max_market_cap: float | None = None,
    min_revenue_growth: float | None = None,
    min_income_growth: float | None = None,
    min_roe: float | None = None,
    max_pe: float | None = None,
    min_average_volume: float | None = None,
    min_price: float | None = None,
    size: int = 250,
    max_results: int = 1000,
    sort_field: str = "totalrevenues1yrgrowth.lasttwelvemonths",
    sort_ascending: bool = False,
) -> dict[str, Any]:
    """Use Yahoo's native EquityQuery screener for a fast first-pass numeric filter.

    Yahoo caps one screener page at 250 results. Pagination is used only up to
    max_results, after which deeper per-company enrichment should begin.
    """
    yf = _require("yfinance", "yfinance")
    EquityQuery = getattr(yf, "EquityQuery", None)
    if EquityQuery is None:
        raise DataSourceUnavailable("Installed yfinance does not expose EquityQuery.")

    operands: list[Any] = []
    if region:
        operands.append(EquityQuery("eq", ["region", region.lower().strip()]))
    if sectors:
        operands.append(EquityQuery("is-in", ["sector", *sectors]))
    if exchanges:
        operands.append(EquityQuery("is-in", ["exchange", *exchanges]))
    if min_market_cap is not None:
        operands.append(EquityQuery("gte", ["intradaymarketcap", float(min_market_cap)]))
    if max_market_cap is not None:
        operands.append(EquityQuery("lte", ["intradaymarketcap", float(max_market_cap)]))
    if min_revenue_growth is not None:
        operands.append(
            EquityQuery("gte", ["totalrevenues1yrgrowth.lasttwelvemonths", float(min_revenue_growth)])
        )
    if min_income_growth is not None:
        operands.append(
            EquityQuery("gte", ["netincome1yrgrowth.lasttwelvemonths", float(min_income_growth)])
        )
    if min_roe is not None:
        operands.append(EquityQuery("gte", ["returnonequity.lasttwelvemonths", float(min_roe)]))
    if max_pe is not None:
        operands.append(EquityQuery("lte", ["peratio.lasttwelvemonths", float(max_pe)]))
    if min_average_volume is not None:
        operands.append(EquityQuery("gte", ["avgdailyvol3m", float(min_average_volume)]))
    if min_price is not None:
        operands.append(EquityQuery("gte", ["intradayprice", float(min_price)]))

    query = EquityQuery("and", operands) if operands else EquityQuery("and", [])
    page_size = max(1, min(int(size), 250))
    cap = max(page_size, min(int(max_results), 2500))
    rows: list[dict[str, Any]] = []

    for offset in range(0, cap, page_size):
        response = yf.screen(
            query,
            offset=offset,
            size=page_size,
            sortField=sort_field,
            sortAsc=sort_ascending,
        )
        quotes = response.get("quotes", []) if isinstance(response, dict) else []
        if not quotes:
            break
        rows.extend(quotes)
        if len(quotes) < page_size:
            break

    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        symbol = str(row.get("symbol") or row.get("ticker") or "").strip().upper()
        if symbol:
            dedup[symbol] = row

    normalized = []
    for symbol, row in dedup.items():
        normalized.append(
            {
                "symbol": symbol,
                "company": row.get("longName") or row.get("shortName") or symbol,
                "exchange": row.get("exchange"),
                "country": row.get("country") or row.get("region"),
                "sector": row.get("sector"),
                "industry": row.get("industry"),
                "market_cap": _finite(row.get("marketCap") or row.get("intradaymarketcap") or row.get("lastCloseMarketCap")),
                "price": _finite(row.get("regularMarketPrice") or row.get("intradayprice") or row.get("eodprice")),
                "revenue_growth_1y": _finite(row.get("totalrevenues1yrgrowth.lasttwelvemonths")),
                "income_growth_1y": _finite(row.get("netincome1yrgrowth.lasttwelvemonths")),
                "roe": _finite(row.get("returnonequity.lasttwelvemonths")),
                "pe_ratio": _finite(row.get("peratio.lasttwelvemonths")),
                "average_volume": _finite(row.get("avgdailyvol3m")),
                "raw": row,
            }
        )

    normalized.sort(
        key=lambda x: (
            -(x.get("revenue_growth_1y") if x.get("revenue_growth_1y") is not None else -10_000),
            x["symbol"],
        )
    )
    return {
        "status": "ok",
        "provider": "yfinance",
        "record_count": len(normalized),
        "records": normalized[:cap],
        "filters": {
            "region": region,
            "sectors": sectors,
            "exchanges": exchanges,
            "min_market_cap": min_market_cap,
            "max_market_cap": max_market_cap,
            "min_revenue_growth": min_revenue_growth,
            "min_income_growth": min_income_growth,
            "min_roe": min_roe,
            "max_pe": max_pe,
            "min_average_volume": min_average_volume,
            "min_price": min_price,
        },
        "provider_limit": "Yahoo screener pages are capped at 250 results.",
    }


def fetch_sec_company_filing(symbol: str, *, form: str = "10-K") -> dict[str, Any]:
    """Retrieve the latest SEC filing through EdgarTools."""
    edgar = _require("edgar", "edgartools")
    import os

    identity = os.getenv("EDGAR_IDENTITY", "").strip()
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


def fetch_macro_series(symbols: str | list[str], *, start: date, end: date) -> dict[str, Any]:
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


def fetch_openbb_coverage() -> dict[str, Any]:
    """Inspect installed OpenBB V5 provider namespaces without guessing commands."""
    openbb = _require("openbb", "openbb")
    from openbb import obb

    coverage = getattr(obb, "coverage", None)
    providers = getattr(coverage, "providers", None) if coverage else None
    return {
        "status": "ok",
        "provider": "OpenBB",
        "providers": providers if isinstance(providers, dict) else str(providers),
        "note": "OpenBB V5 is a provider-extension layer; actual dataset coverage depends on installed provider packages.",
    }


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

    # VectorBT community edition is excellent for experimentation but has Commons
    # Clause restrictions; ASET should not silently bundle it into commercial products.
    if status["vectorbt"]:
        return {"selected": "vectorbt", "status": status, "reason": "fast vectorized workflow available; review its license before resale"}
    if status["backtrader"]:
        return {"selected": "backtrader", "status": status, "reason": "event-driven engine available"}
    if status["lean_cli"]:
        return {"selected": "lean_cli", "status": status, "reason": "LEAN CLI available"}
    return {"selected": None, "status": status, "reason": "no quant engine installed"}


def source_engine_status() -> dict[str, Any]:
    """Return runtime status for data and quant projects without importing everything."""
    return {
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


__all__ = [
    "DataSourceUnavailable",
    "choose_backtest_engine",
    "fetch_macro_series",
    "fetch_openbb_coverage",
    "fetch_sec_company_filing",
    "fetch_universe_financedatabase",
    "fetch_yfinance_fundamentals",
    "fetch_yfinance_fundamentals_many",
    "fetch_yfinance_prices",
    "screen_yfinance_equities",
    "source_engine_status",
]
