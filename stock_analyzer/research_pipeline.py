"""Automatic public-equity dataset and screening pipeline.

The pipeline is intentionally staged so expensive per-company requests happen only
after broad, fast filtering. Every stage returns counts, selected sources and failures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_router import route_workflow
from .multibagger_scoring import rank_multibagger_candidates
from .source_adapters import (
    DataSourceUnavailable,
    fetch_sec_company_filing,
    fetch_universe_financedatabase,
    fetch_yfinance_fundamentals_many,
    screen_yfinance_equities,
)


@dataclass(frozen=True)
class MultibaggerPipelineConfig:
    region: str = "global"
    universe_limit: int = 20_000
    fast_screen_limit: int = 1_000
    fundamentals_limit: int = 50
    top_k: int = 20
    max_workers: int = 8
    verify_us_filings: int = 0


def _to_iso_country(region: str) -> str | None:
    value = region.strip().lower()
    if value in ("global", "world", "worldwide", ""):
        return None
    return {
        "us": "us",
        "united_states": "us",
        "usa": "us",
        "india": "in",
        "in": "in",
        "china": "cn",
        "cn": "cn",
        "hong_kong": "hk",
        "hk": "hk",
        "uk": "gb",
        "united_kingdom": "gb",
        "germany": "de",
        "france": "fr",
        "japan": "jp",
        "south_korea": "kr",
        "canada": "ca",
        "australia": "au",
        "singapore": "sg",
        "taiwan": "tw",
    }.get(value, value if len(value) == 2 else None)


def _normalize_yfinance_company(result: dict[str, Any]) -> dict[str, Any]:
    def clean_key(value: Any) -> str:
        return "".join(ch for ch in str(value).lower() if ch.isalnum())

    def to_date(value: Any) -> str:
        text = str(value)
        return text[:10]

    def first_numeric(item: dict[str, Any], candidates: tuple[str, ...]) -> float | None:
        wanted = {clean_key(x) for x in candidates}
        for key, value in item.items():
            if clean_key(key) in wanted and isinstance(value, (int, float)):
                return float(value)
        return None

    income_rows = result.get("income_statement") or []
    balance_rows = result.get("balance_sheet") or []

    history: list[dict[str, Any]] = []
    for row in income_rows:
        period = row.get("period")
        revenue = first_numeric(row, ("TotalRevenue", "Total Revenue", "OperatingRevenue", "Operating Revenue"))
        net_income = first_numeric(row, ("NetIncome", "Net Income", "NetIncomeCommonStockholders", "Net Income Common Stockholders"))
        if period and (revenue is not None or net_income is not None):
            history.append(
                {
                    "fiscal_date": to_date(period),
                    "revenue": revenue,
                    "net_income": net_income,
                }
            )
    history.sort(key=lambda x: x["fiscal_date"], reverse=True)

    latest_revenue = history[0]["revenue"] if history else None
    latest_income = history[0]["net_income"] if history else None
    prior_income = history[1]["net_income"] if len(history) > 1 else None
    income_growth = (
        latest_income / prior_income - 1
        if latest_income is not None and prior_income not in (None, 0)
        else None
    )
    average_income = (
        sum(x["net_income"] for x in history[:5] if x["net_income"] is not None)
        / len([x for x in history[:5] if x["net_income"] is not None])
        if any(x["net_income"] is not None for x in history[:5])
        else None
    )

    balance_latest = balance_rows[0] if balance_rows else {}
    debt = first_numeric(
        balance_latest,
        ("TotalDebt", "Total Debt", "LongTermDebt", "Long Term Debt"),
    )
    cash = first_numeric(
        balance_latest,
        ("CashCashEquivalentsAndShortTermInvestments", "Cash Cash Equivalents And Short Term Investments",
         "TotalCashAndShortTermInvestments", "Total Cash And Short Term Investments"),
    )
    debt_cash = debt / cash if debt is not None and cash not in (None, 0) else None

    profile = result.get("profile") or {}
    market_cap = profile.get("market_cap")

    valuation_rows = result.get("valuation") or []
    current_pe = None
    for row in valuation_rows:
        current_pe = first_numeric(
            row,
            ("TrailingPE", "PeRatio", "PERatio", "TrailingPe", "PriceEarnings"),
        )
        if current_pe is not None:
            break

    margin = latest_income / latest_revenue if latest_income is not None and latest_revenue not in (None, 0) else None

    return {
        "symbol": result.get("symbol"),
        "company": profile.get("name") or result.get("symbol"),
        "country": profile.get("country"),
        "exchange": profile.get("exchange"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "fundamentals": {
            "revenue": latest_revenue,
            "net_income": latest_income,
            "net_margin": margin,
            "income_growth": income_growth,
            "average_5y_net_income": average_income,
            "debt": debt,
            "cash": cash,
            "debt_cash": debt_cash,
            "market_cap": market_cap,
            "pe_ratio": current_pe,
            "market_cap_to_income": (
                market_cap / latest_income
                if isinstance(market_cap, (int, float)) and latest_income not in (None, 0)
                else None
            ),
        },
        "income_history": history[:5],
        "flags": [],
        "meta": {
            "provider": "yfinance",
            "observed_at": result.get("observed_at"),
        },
    }


def run_multibagger_pipeline(
    *,
    config: MultibaggerPipelineConfig | None = None,
    country: str | None = None,
    exchange: str | None = None,
    sector: str | None = None,
    industry: str | None = None,
    market_cap_categories: list[str] | None = None,
    min_market_cap: float | None = None,
    max_market_cap: float | None = None,
    min_revenue_growth: float | None = 10.0,
    min_income_growth: float | None = 10.0,
    min_roe: float | None = 10.0,
    max_pe: float | None = 60.0,
) -> dict[str, Any]:
    """Run the fast-to-deep public-equity candidate funnel."""
    cfg = config or MultibaggerPipelineConfig()
    route = route_workflow("multibagger stock screening", region=cfg.region, scale="xlarge", stage="screen")

    audit: dict[str, Any] = {
        "workflow": route,
        "stages": [],
        "warnings": [],
    }

    # Stage 1: broad, cheap metadata universe.
    universe_result: dict[str, Any]
    try:
        universe_result = fetch_universe_financedatabase(
            country=country,
            exchange=exchange,
            sector=sector,
            industry=industry,
            market_cap_categories=market_cap_categories,
            only_primary_listing=True,
            include_delisted=False,
            limit=cfg.universe_limit,
        )
    except (DataSourceUnavailable, ValueError) as exc:
        universe_result = {"status": "unavailable", "error": str(exc)}

    audit["stages"].append(
        {
            "name": "universe_discovery",
            "source": universe_result.get("source", "FinanceDatabase"),
            "status": universe_result.get("status"),
            "record_count": universe_result.get("record_count", 0),
        }
    )

    universe_records = universe_result.get("records") or []
    universe_symbols = []
    for row in universe_records:
        symbol = str(row.get("symbol") or "").strip().upper()
        if symbol and symbol not in universe_symbols:
            universe_symbols.append(symbol)

    # Stage 2: fast numeric screening. This is intentionally independent of
    # per-company financial statements and uses provider-native screen fields.
    region_code = _to_iso_country(cfg.region)
    try:
        fast = screen_yfinance_equities(
            region=region_code,
            sectors=[sector] if sector else None,
            exchanges=[exchange] if exchange else None,
            min_market_cap=min_market_cap,
            max_market_cap=max_market_cap,
            min_revenue_growth=min_revenue_growth,
            min_income_growth=min_income_growth,
            min_roe=min_roe,
            max_pe=max_pe,
            min_price=1.0,
            size=250,
            max_results=cfg.fast_screen_limit,
        )
    except Exception as exc:
        fast = {"status": "error", "provider": "yfinance", "records": [], "error": str(exc)}

    fast_records = fast.get("records") or []
    fast_symbols = {str(row.get("symbol") or "").strip().upper() for row in fast_records}

    # Prefer exact intersection with the broad metadata universe. If that is
    # unavailable, keep the fast provider candidates but label the fallback.
    if universe_symbols:
        selected_symbols = [s for s in fast_symbols if s in set(universe_symbols)]
        if not selected_symbols:
            selected_symbols = [s for s in fast_symbols if s]
            audit["warnings"].append("Fast screener had no symbol intersection with FinanceDatabase; used fast-screener candidates as fallback.")
    else:
        selected_symbols = [s for s in fast_symbols if s]
        audit["warnings"].append("FinanceDatabase universe was unavailable; using yfinance screener as universe fallback.")

    # Preserve the provider's own ranking, then bound costly fundamentals calls.
    fast_rank = {
        str(row.get("symbol") or "").strip().upper(): row
        for row in fast_records
        if row.get("symbol")
    }
    selected_symbols.sort(
        key=lambda symbol: (
            -(fast_rank.get(symbol, {}).get("revenue_growth_1y") or -10_000),
            symbol,
        )
    )
    selected_symbols = selected_symbols[: max(1, min(cfg.fundamentals_limit, 250))]

    audit["stages"].append(
        {
            "name": "fast_numeric_screen",
            "source": "yfinance",
            "status": fast.get("status"),
            "record_count": len(fast_records),
            "selected_for_deep_enrichment": len(selected_symbols),
        }
    )

    # Stage 3: bounded deep fundamentals enrichment.
    try:
        enriched = fetch_yfinance_fundamentals_many(selected_symbols, max_workers=cfg.max_workers)
    except Exception as exc:
        enriched = {"status": "error", "results": [], "failures": [], "error": str(exc)}

    rows = [_normalize_yfinance_company(item) for item in (enriched.get("results") or [])]
    ranked = rank_multibagger_candidates(rows, top_k=cfg.top_k)

    audit["stages"].append(
        {
            "name": "deep_fundamentals",
            "source": "yfinance",
            "status": enriched.get("status"),
            "requested": len(selected_symbols),
            "succeeded": enriched.get("succeeded_symbols", 0),
            "failed": enriched.get("failed_symbols", 0),
        }
    )

    # Stage 4: primary-source verification queue is bounded and optional.
    verification_queue = []
    if cfg.verify_us_filings > 0:
        for candidate in ranked[: cfg.verify_us_filings]:
            if str(candidate.get("country") or "").casefold() in {"united states", "usa", "us"}:
                verification_queue.append(candidate["symbol"])

    filing_checks: list[dict[str, Any]] = []
    for symbol in verification_queue:
        try:
            filing_checks.append(fetch_sec_company_filing(symbol, form="10-K"))
        except Exception as exc:
            filing_checks.append(
                {
                    "symbol": symbol,
                    "status": "unavailable",
                    "error": str(exc),
                }
            )

    if verification_queue:
        audit["stages"].append(
            {
                "name": "primary_filing_queue",
                "source": "EdgarTools",
                "requested": len(verification_queue),
                "completed": sum(x.get("status") == "ok" for x in filing_checks),
                "failed": sum(x.get("status") != "ok" for x in filing_checks),
            }
        )

    return {
        "status": "ok" if ranked else "no_candidates",
        "objective": "Research-priority multi-year compounding candidate discovery",
        "candidates": ranked,
        "verification_queue": verification_queue,
        "filing_checks": filing_checks,
        "audit": audit,
        "disclaimer": "This pipeline identifies research candidates. It does not predict guaranteed multibagger returns or provide personalized investment advice.",
    }


__all__ = ["MultibaggerPipelineConfig", "run_multibagger_pipeline"]
