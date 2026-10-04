"""Automatic dataset/source routing for ASET.

This module deliberately separates:
- universe metadata discovery;
- live market/fundamental retrieval;
- filings;
- macro data;
- backtest engines.

No source is treated as universally authoritative. The router chooses sources by
capability, geography, scale, optional-package availability and configured
credentials, and returns an auditable plan instead of silently guessing.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import os
import re
import shutil
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from .providers import MarketDataProvider


class DatasetKind(StrEnum):
    UNIVERSE = "universe"
    PRICES = "prices"
    FUNDAMENTALS = "fundamentals"
    FILINGS = "filings"
    MACRO = "macro"
    BACKTEST = "backtest"


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    project: str
    dataset_kinds: tuple[DatasetKind, ...]
    regions: tuple[str, ...]
    bulk: bool
    preferred_stages: tuple[str, ...]
    optional_module: str | None = None
    credential_env: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class DatasetRequest:
    kind: DatasetKind
    region: str = "global"
    scale: str = "medium"
    stage: str = "screen"
    requires_fresh: bool = True


SOURCE_REGISTRY: tuple[SourceSpec, ...] = (
    SourceSpec(
        "finance_database",
        "FinanceDatabase",
        (DatasetKind.UNIVERSE,),
        ("global",),
        True,
        ("discover", "screen"),
        "financedatabase",
        notes="Broad instrument metadata and filtering; not a live fundamentals feed.",
    ),
    SourceSpec(
        "yfinance_prices",
        "yfinance",
        (DatasetKind.PRICES,),
        ("global",),
        True,
        ("screen", "deep_dive"),
        "yfinance",
        notes="Broad batch historical-price retrieval; useful for first-pass price/liquidity signals.",
    ),
    SourceSpec(
        "yfinance_screener",
        "yfinance",
        (DatasetKind.UNIVERSE, DatasetKind.FUNDAMENTALS),
        ("global",),
        True,
        ("screen", "deep_dive"),
        "yfinance",
        notes="Native Yahoo equity screener; custom queries support growth, valuation, leverage, profitability and liquidity fields; page size is provider-limited.",
    ),
    SourceSpec(
        "akshare",
        "AKShare",
        (DatasetKind.UNIVERSE, DatasetKind.PRICES, DatasetKind.FUNDAMENTALS),
        ("china", "hong_kong"),
        True,
        ("screen", "deep_dive"),
        "akshare",
        notes="Strong China-market coverage; interface availability can vary by upstream source.",
    ),
    SourceSpec(
        "edgartools",
        "EdgarTools",
        (DatasetKind.FUNDAMENTALS, DatasetKind.FILINGS),
        ("united_states",),
        False,
        ("deep_dive", "verification"),
        "edgar",
        credential_env="EDGAR_IDENTITY",
        notes="Primary SEC EDGAR filing and XBRL research for U.S. issuers.",
    ),
    SourceSpec(
        "sec_edgar_downloader",
        "sec-edgar-downloader",
        (DatasetKind.FILINGS,),
        ("united_states",),
        False,
        ("verification",),
        "sec_edgar_downloader",
        credential_env="EDGAR_IDENTITY",
        notes="Raw SEC filing retrieval fallback/ingestion layer.",
    ),
    SourceSpec(
        "pandas_datareader",
        "pandas-datareader",
        (DatasetKind.MACRO,),
        ("global",),
        True,
        ("macro",),
        "pandas_datareader",
        notes="Use for maintained macro/statistical sources rather than securities readers.",
    ),
    SourceSpec(
        "openbb",
        "OpenBB Platform",
        (DatasetKind.UNIVERSE, DatasetKind.PRICES, DatasetKind.FUNDAMENTALS, DatasetKind.FILINGS, DatasetKind.MACRO),
        ("global",),
        True,
        ("discover", "screen", "deep_dive", "verification"),
        "openbb",
        notes="Optional aggregation layer; the installed provider packages determine actual coverage.",
    ),
    SourceSpec(
        "vectorbt",
        "VectorBT",
        (DatasetKind.BACKTEST,),
        ("global",),
        True,
        ("backtest",),
        "vectorbt",
        notes="Fast vectorized research/backtesting engine; community edition licensing must be reviewed for commercial distribution.",
    ),
    SourceSpec(
        "backtrader",
        "Backtrader",
        (DatasetKind.BACKTEST,),
        ("global",),
        False,
        ("backtest",),
        "backtrader",
        notes="Event-driven backtesting engine; data feeds are supplied separately.",
    ),
    SourceSpec(
        "lean",
        "QuantConnect LEAN",
        (DatasetKind.BACKTEST,),
        ("global",),
        True,
        ("backtest", "optimization"),
        "AlgorithmImports",
        notes="Optional professional-grade open-source engine; typically installed/run through the LEAN CLI.",
    ),
    SourceSpec(
        "fixture",
        "ASET Fixture Provider",
        (DatasetKind.PRICES,),
        ("global",),
        True,
        ("development",),
        "stock_analyzer.providers",
        notes="Deterministic demo/test data only; never acceptable as live evidence.",
    ),
)


KEYWORDS: dict[str, DatasetKind] = {
    "universe": DatasetKind.UNIVERSE,
    "dataset": DatasetKind.UNIVERSE,
    "screen": DatasetKind.UNIVERSE,
    "screener": DatasetKind.UNIVERSE,
    "tickers": DatasetKind.UNIVERSE,
    "price": DatasetKind.PRICES,
    "prices": DatasetKind.PRICES,
    "growth": DatasetKind.FUNDAMENTALS,
    "quality": DatasetKind.FUNDAMENTALS,
    "quote": DatasetKind.PRICES,
    "fundamental": DatasetKind.FUNDAMENTALS,
    "fundamentals": DatasetKind.FUNDAMENTALS,
    "financials": DatasetKind.FUNDAMENTALS,
    "earnings": DatasetKind.FUNDAMENTALS,
    "filing": DatasetKind.FILINGS,
    "filings": DatasetKind.FILINGS,
    "10-k": DatasetKind.FILINGS,
    "10q": DatasetKind.FILINGS,
    "sec": DatasetKind.FILINGS,
    "macro": DatasetKind.MACRO,
    "fred": DatasetKind.MACRO,
    "backtest": DatasetKind.BACKTEST,
    "backtesting": DatasetKind.BACKTEST,
    "optimize": DatasetKind.BACKTEST,
}


def installed(module_name: str | None) -> bool:
    if not module_name:
        return True
    return importlib.util.find_spec(module_name) is not None


def package_version(module_name: str | None) -> str | None:
    if not module_name:
        return None
    distribution_names = {
        "financedatabase": "financedatabase",
        "yfinance": "yfinance",
        "akshare": "akshare",
        "edgar": "edgartools",
        "sec_edgar_downloader": "sec-edgar-downloader",
        "pandas_datareader": "pandas-datareader",
        "openbb": "openbb",
        "vectorbt": "vectorbt",
        "backtrader": "backtrader",
        "AlgorithmImports": "lean",
    }
    try:
        return importlib.metadata.version(distribution_names.get(module_name, module_name))
    except importlib.metadata.PackageNotFoundError:
        return None


def credential_ready(spec: SourceSpec) -> bool:
    if not spec.credential_env:
        return True
    return bool(os.getenv(spec.credential_env, "").strip())


def source_health(spec: SourceSpec) -> dict[str, Any]:
    available = installed(spec.optional_module)
    version = package_version(spec.optional_module)
    credential = credential_ready(spec)
    status = "ready" if available and credential else "unavailable"
    if available and spec.credential_env and not credential:
        status = "needs_configuration"
    if spec.source_id == "fixture":
        status = "development_only"
    if spec.source_id == "lean":
        available = shutil.which("lean") is not None
        version = None
        if available:
            try:
                version = importlib.metadata.version("lean")
            except importlib.metadata.PackageNotFoundError:
                version = "cli-installed"
        status = "ready" if available else "unavailable"
    return {
        **asdict(spec),
        "dataset_kinds": [x.value for x in spec.dataset_kinds],
        "installed": available,
        "version": version,
        "credential_ready": credential,
        "status": status,
    }


def all_source_health() -> list[dict[str, Any]]:
    return [source_health(spec) for spec in SOURCE_REGISTRY]


def infer_kind(task: str, default: DatasetKind = DatasetKind.UNIVERSE) -> DatasetKind:
    text = task.lower()
    for keyword, kind in KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            if kind == DatasetKind.BACKTEST and any(x in text for x in ("stock", "company", "fundamental")):
                continue
            return kind
    return default


def normalize_region(region: str) -> str:
    value = region.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "us": "united_states",
        "usa": "united_states",
        "america": "united_states",
        "cn": "china",
        "china_a": "china",
        "hk": "hong_kong",
        "hongkong": "hong_kong",
        "world": "global",
        "worldwide": "global",
        "all": "global",
    }
    return aliases.get(value, value or "global")


def _score(spec: SourceSpec, request: DatasetRequest) -> tuple[int, list[str]]:
    health = source_health(spec)
    reasons: list[str] = []
    score = 0

    if request.kind in spec.dataset_kinds:
        score += 100
        reasons.append("dataset capability")
    else:
        return -1, ["unsupported dataset"]

    region = normalize_region(request.region)
    if region in spec.regions:
        score += 30
        reasons.append("region match")
    elif "global" in spec.regions:
        score += 5
        reasons.append("global coverage fallback")
    else:
        return -1, ["region mismatch"]

    if request.scale in ("large", "xlarge") and spec.bulk:
        score += 20
        reasons.append("bulk capable")

    if request.stage in spec.preferred_stages:
        score += 15
        reasons.append("stage match")

    if health["installed"]:
        score += 50
        reasons.append("installed")
    else:
        score -= 100
        reasons.append("package unavailable")

    if health["status"] == "needs_configuration":
        score -= 80
        reasons.append("credential/configuration missing")
    elif health["status"] == "development_only" and request.stage not in ("development",):
        score -= 200
        reasons.append("development-only source")

    if request.requires_fresh and spec.source_id == "finance_database":
        score -= 20
        reasons.append("metadata source is not a live fundamentals feed")

    if request.kind == DatasetKind.FILINGS and spec.source_id == "edgartools":
        score += 25
        reasons.append("primary filing/XBRL source")

    if request.kind == DatasetKind.PRICES and spec.source_id == "yfinance_prices":
        score += 20
        reasons.append("broad batch price coverage")
    if request.kind == DatasetKind.FUNDAMENTALS and spec.source_id == "yfinance_screener":
        score += 25
        reasons.append("native bulk fundamentals screening")

    return score, reasons


def route(request: DatasetRequest) -> dict[str, Any]:
    candidates = []
    for spec in SOURCE_REGISTRY:
        score_value, reasons = _score(spec, request)
        if score_value >= 0:
            candidates.append({
                "source_id": spec.source_id,
                "project": spec.project,
                "score": score_value,
                "reasons": reasons,
                "status": source_health(spec)["status"],
            })
    candidates.sort(key=lambda item: (-item["score"], item["source_id"]))

    ready = [x for x in candidates if x["status"] == "ready"]
    plan = []
    if ready:
        primary = ready[0]
        plan.append(primary | {"role": "primary"})
        for candidate in ready[1:3]:
            plan.append(candidate | {"role": "fallback_or_crosscheck"})
    else:
        plan = candidates[:3]

    return {
        "request": {
            "kind": request.kind.value,
            "region": normalize_region(request.region),
            "scale": request.scale,
            "stage": request.stage,
            "requires_fresh": request.requires_fresh,
        },
        "selected": plan,
        "all_ranked_candidates": candidates[:10],
        "policy": [
            "Never use a source that is unavailable or missing required credentials.",
            "Prefer bulk-capable sources for large universes.",
            "Use FinanceDatabase for universe metadata/filtering, not as live fundamentals.",
            "Use primary filings for material U.S. issuer claims.",
            "Cross-check material financial figures when independent sources disagree.",
            "Never fill missing values with model guesses.",
            "Do not use fixture data outside development/tests.",
        ],
    }


def route_workflow(
    task: str,
    region: str = "global",
    scale: str = "medium",
    stage: str = "screen",
) -> dict[str, Any]:
    text = task.lower()
    normalized_region = normalize_region(region)
    stages: list[DatasetRequest] = []

    if any(word in text for word in ("backtest", "backtesting", "strategy")):
        stages = [
            DatasetRequest(DatasetKind.PRICES, normalized_region, scale, "screen", True),
            DatasetRequest(DatasetKind.BACKTEST, normalized_region, scale, "backtest", False),
        ]
    elif any(word in text for word in ("filing", "10-k", "10-q", "edgar")):
        stages = [
            DatasetRequest(DatasetKind.FUNDAMENTALS, normalized_region, "small", "deep_dive", True),
            DatasetRequest(DatasetKind.FILINGS, normalized_region, "small", "verification", True),
        ]
    elif any(word in text for word in ("multibagger", "compounder", "growth stock", "stock screen", "screener")):
        stages = [
            DatasetRequest(DatasetKind.UNIVERSE, normalized_region, scale, "discover", False),
            DatasetRequest(DatasetKind.FUNDAMENTALS, normalized_region, "large", "screen", True),
            DatasetRequest(DatasetKind.PRICES, normalized_region, "large", "screen", True),
            DatasetRequest(
                DatasetKind.FILINGS,
                normalized_region,
                "small",
                "verification",
                True,
            ),
        ]
        if normalized_region == "global":
            stages[-1] = DatasetRequest(DatasetKind.FILINGS, normalized_region, "small", "verification", True)
    else:
        stages = [DatasetRequest(infer_kind(task), normalized_region, scale, stage, True)]

    return {
        "task": task,
        "region": normalized_region,
        "workflow": [
            {
                "stage": request.kind.value,
                "request": route(request),
            }
            for request in stages
        ],
        "policy": [
            "Use broad metadata first; do not hit expensive per-company endpoints before filtering.",
            "Use native bulk screeners when available for first-pass numeric filtering.",
            "Only enrich a bounded shortlist with slow fundamentals/filings endpoints.",
            "Cross-check material facts with independent sources before final ranking.",
            "Never use fixture data as live evidence.",
        ],
    }


def route_task(task: str, region: str = "global", scale: str = "medium", stage: str = "screen") -> dict[str, Any]:
    return route_workflow(task, region=region, scale=scale, stage=stage)


def _filter_value(frame: Any, column: str, value: Any) -> Any:
    if value is None or column not in frame.columns:
        return frame
    if isinstance(value, str):
        return frame[frame[column].astype(str).str.casefold() == value.casefold()]
    return frame


def filter_finance_database(
    *,
    country: str | None = None,
    exchange: str | None = None,
    sector: str | None = None,
    industry: str | None = None,
    min_market_cap: float | None = None,
    max_market_cap: float | None = None,
    only_primary_listing: bool = True,
    include_delisted: bool = False,
    market_cap_categories: list[str] | None = None,
    limit: int = 10_000,
) -> dict[str, Any]:
    """Filter FinanceDatabase metadata without pretending it is live fundamentals."""
    if not installed("financedatabase"):
        return {
            "status": "unavailable",
            "source": "FinanceDatabase",
            "error": "financedatabase package is not installed",
            "install_extra": "pip install -e '.[universe]'",
        }

    import financedatabase as fd

    equities = fd.Equities()
    kwargs: dict[str, Any] = {}
    if country:
        kwargs["country"] = country
    if exchange:
        kwargs["exchange"] = exchange
    if sector:
        kwargs["sector"] = sector
    if industry:
        kwargs["industry"] = industry
    if only_primary_listing:
        kwargs["only_primary_listing"] = True

    frame = equities.select(**kwargs)
    if frame is None:
        frame = __import__("pandas").DataFrame()

    if market_cap_categories and "market_cap" in frame.columns:
        normalized = {str(x).strip().casefold() for x in market_cap_categories if str(x).strip()}
        actual = frame["market_cap"].astype(str).str.strip().str.casefold()
        frame = frame[actual.isin(normalized)]

    if not include_delisted and "delisted" in frame.columns:
        values = frame["delisted"].astype(str).str.strip().str.lower()
        frame = frame[~values.isin({"true", "1", "yes", "y"})]

    if min_market_cap is not None or max_market_cap is not None:
        # FinanceDatabase market_cap is a categorical size bucket, not a numeric valuation.
        raise ValueError(
            "FinanceDatabase market_cap is categorical. Use market_cap_categories instead of numeric min/max values."
        )

    frame = frame.head(max(1, min(int(limit), 100_000)))
    records = frame.reset_index().to_dict(orient="records")
    return {
        "status": "ok",
        "source": "FinanceDatabase",
        "project": "JerBouma/FinanceDatabase",
        "record_count": len(records),
        "records": records,
        "freshness": "metadata snapshot; not a live fundamentals feed",
        "next_stage": route_workflow("price and fundamental screen", region=country or "global", scale="large", stage="screen"),
    }


def provider_project_map() -> dict[str, str]:
    return {spec.source_id: spec.project for spec in SOURCE_REGISTRY}


__all__ = [
    "DatasetKind",
    "DatasetRequest",
    "SourceSpec",
    "SOURCE_REGISTRY",
    "all_source_health",
    "filter_finance_database",
    "infer_kind",
    "provider_project_map",
    "route",
    "route_task",
    "route_workflow",
    "source_health",
]
