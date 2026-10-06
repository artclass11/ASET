from __future__ import annotations

from math import isfinite
from typing import Any, Iterable


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _growth_score(cagr: float | None) -> float | None:
    if cagr is None:
        return None
    # Screening scale: -10% -> 0, 30% -> 100. This is a prioritization aid,
    # not a claim that these growth bands are intrinsically good or bad.
    return _clamp((cagr + 0.10) / 0.40 * 100.0)


def _valuation_score(pe: float | None, cap_income: float | None) -> float | None:
    value = pe if pe is not None and pe > 0 else cap_income if cap_income is not None and cap_income > 0 else None
    if value is None:
        return None
    if value <= 10:
        return 100.0
    if value <= 15:
        return 90.0
    if value <= 25:
        return 75.0
    if value <= 40:
        return 55.0
    if value <= 60:
        return 35.0
    if value <= 100:
        return 15.0
    return 0.0


def _balance_score(debt_cash: float | None, debt: float | None, cash: float | None) -> float | None:
    if debt_cash is not None:
        if debt_cash <= 0.25:
            return 100.0
        if debt_cash <= 1:
            return 85.0
        if debt_cash <= 2:
            return 65.0
        if debt_cash <= 3:
            return 40.0
        return 10.0
    if debt is not None and cash is not None:
        return 90.0 if cash > debt else 40.0
    return None


def _cagr(values: list[float], years: int | None = None) -> float | None:
    clean = [v for v in values if v is not None and isfinite(v)]
    if len(clean) < 2 or clean[-1] <= 0 or clean[0] <= 0:
        return None
    period = years if years is not None else len(clean) - 1
    if period <= 0:
        return None
    return (clean[-1] / clean[0]) ** (1.0 / period) - 1.0


def _history_metrics(row: dict[str, Any]) -> dict[str, Any]:
    history = row.get("income_history") or []
    ordered = []
    for item in history:
        revenue = _number(item.get("revenue"))
        income = _number(item.get("net_income"))
        if item.get("fiscal_date") and (revenue is not None or income is not None):
            ordered.append(
                {
                    "fiscal_date": item.get("fiscal_date"),
                    "revenue": revenue,
                    "net_income": income,
                }
            )
    ordered = ordered[:5]
    # SignalDesk emits latest-to-oldest rows. Reverse only when dates are usable.
    if len(ordered) >= 2 and ordered[0]["fiscal_date"] > ordered[-1]["fiscal_date"]:
        chronological = list(reversed(ordered))
    else:
        chronological = ordered

    revenue_series = [x["revenue"] for x in chronological if x["revenue"] is not None]
    income_series = [x["net_income"] for x in chronological if x["net_income"] is not None]
    positive_years = sum(1 for x in income_series if x > 0)
    margin_series = [
        x["net_income"] / x["revenue"]
        for x in chronological
        if x["net_income"] is not None and x["revenue"] not in (None, 0)
    ]

    return {
        "observations": len(chronological),
        "revenue_cagr": _cagr(revenue_series),
        "net_income_cagr": _cagr(income_series),
        "positive_profit_years": positive_years,
        "positive_profit_ratio": (positive_years / len(income_series)) if income_series else None,
        "margin_start": margin_series[0] if margin_series else None,
        "margin_end": margin_series[-1] if margin_series else None,
        "margin_delta": (margin_series[-1] - margin_series[0]) if len(margin_series) >= 2 else None,
    }


def score_candidate(row: dict[str, Any]) -> dict[str, Any]:
    fundamentals = row.get("fundamentals") or {}
    history = _history_metrics(row)

    net_margin = _number(fundamentals.get("net_margin"))
    income_growth = _number(fundamentals.get("income_growth"))
    pe_ratio = _number(fundamentals.get("pe_ratio"))
    cap_income = _number(fundamentals.get("market_cap_to_income"))
    debt_cash = _number(fundamentals.get("debt_cash"))
    debt = _number(fundamentals.get("debt"))
    cash = _number(fundamentals.get("cash"))
    market_cap = _number(fundamentals.get("market_cap"))

    provenance = {
        "provider": row.get("provider"),
        "source": row.get("source"),
        "fetched_at": row.get("fetched_at"),
        "freshness": row.get("freshness"),
        "quality": row.get("quality"),
        "source_metadata": row.get("source_metadata"),
    }
    provenance = {key: value for key, value in provenance.items() if value is not None}

    growth_parts = [
        x for x in (
            _growth_score(history["revenue_cagr"]),
            _growth_score(history["net_income_cagr"]),
            _growth_score(income_growth),
        ) if x is not None
    ]
    growth_score = sum(growth_parts) / len(growth_parts) if growth_parts else None

    consistency = history["positive_profit_ratio"]
    consistency_score = consistency * 100.0 if consistency is not None else None
    margin_score = None
    if net_margin is not None:
        margin_score = _clamp((net_margin + 0.05) / 0.35 * 100.0)

    quality_parts = [x for x in (consistency_score, margin_score) if x is not None]
    quality_score = sum(quality_parts) / len(quality_parts) if quality_parts else None

    balance_score = _balance_score(debt_cash, debt, cash)
    valuation_score = _valuation_score(pe_ratio, cap_income)

    evidence_fields = (
        fundamentals.get("revenue"),
        fundamentals.get("net_income"),
        fundamentals.get("average_5y_net_income"),
        market_cap,
        net_margin,
        debt,
        cash,
        history["net_income_cagr"],
    )
    evidence_score = sum(x is not None for x in evidence_fields) / len(evidence_fields) * 100.0

    parts: list[tuple[float, float]] = []
    for score, weight in (
        (growth_score, 0.40),
        (quality_score, 0.25),
        (balance_score, 0.15),
        (valuation_score, 0.15),
        (evidence_score, 0.05),
    ):
        if score is not None:
            parts.append((score, weight))

    total_weight = sum(weight for _, weight in parts)
    composite = sum(score * weight for score, weight in parts) / total_weight if total_weight else 0.0

    flags = list(row.get("flags") or [])
    risks: list[str] = []
    if history["net_income_cagr"] is None:
        risks.append("five-year profit CAGR unavailable or not meaningful")
    if history["revenue_cagr"] is None:
        risks.append("five-year revenue CAGR unavailable or not meaningful")
    if debt_cash is not None and debt_cash > 3:
        risks.append("high debt/cash")
    if pe_ratio is not None and pe_ratio > 60:
        risks.append("valuation is high on trailing provider P/E")
    if consistency is not None and consistency < 0.8:
        risks.append("profit consistency below 80% of available years")
    if net_margin is not None and net_margin < 0:
        risks.append("negative net margin")
    risks.extend(x for x in flags if x not in risks)

    if composite >= 75:
        tier = "A - immediate research candidate"
    elif composite >= 60:
        tier = "B - watchlist / needs trigger"
    elif composite >= 45:
        tier = "C - screen flag only"
    else:
        tier = "Reject"

    return {
        "symbol": row.get("symbol"),
        "company": row.get("company") or row.get("symbol"),
        "country": row.get("country"),
        "exchange": row.get("exchange"),
        "sector": row.get("sector"),
        "industry": row.get("industry"),
        "market_cap": market_cap,
        "score": round(composite, 2),
        "tier": tier,
        "signals": {
            "revenue_cagr_5y": history["revenue_cagr"],
            "net_income_cagr_5y": history["net_income_cagr"],
            "latest_income_growth": income_growth,
            "net_margin": net_margin,
            "profit_consistency": consistency,
            "margin_delta": history["margin_delta"],
            "debt_cash": debt_cash,
            "pe_ratio": pe_ratio,
            "market_cap_to_income": cap_income,
            "evidence_completeness": round(evidence_score, 2),
        },
        "risk_flags": risks,
        "provenance": provenance,
        "why_it_surfaced": (
            "High screening score driven by the strongest available mix of "
            "multi-year growth, profitability, balance-sheet resilience and valuation signals."
            if composite >= 60
            else (
                "Quantitative signals surfaced the company, but the evidence is not strong enough "
                "for immediate deep research."
            )
        ),
        "must_verify": [
            "durable competitive advantage and reinvestment runway",
            "addressable market and evidence that growth reaches reported revenue",
            "management capital allocation and dilution/share-count history",
            "customer/product concentration and cyclicality",
            "valuation versus normalized earnings/free cash flow and realistic expectations",
            "governance, accounting quality, liquidity and regulatory risks",
            "dated catalysts that can change estimates rather than only a narrative theme",
        ],
        "status": "research candidate" if composite >= 60 else "screen flag",
        "disclaimer": (
            "Deterministic screening signal only; not a forecast, recommendation, "
            "or guarantee of multi-bagger returns."
        ),
    }


def rank_multibagger_candidates(
    rows: Iterable[dict[str, Any]],
    top_k: int = 20,
) -> list[dict[str, Any]]:
    scored = [score_candidate(row) for row in rows]
    scored.sort(key=lambda x: (-x["score"], x["symbol"] or ""))
    return scored[: max(1, min(int(top_k), 100))]


def compare_payloads(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        scored = score_candidate(row)
        signals = scored["signals"]
        result.append(
            {
                "symbol": scored["symbol"],
                "company": scored["company"],
                "sector": scored["sector"],
                "country": scored["country"],
                "market_cap": scored["market_cap"],
                "multibagger_screen_score": scored["score"],
                "tier": scored["tier"],
                "revenue_cagr_5y": signals["revenue_cagr_5y"],
                "net_income_cagr_5y": signals["net_income_cagr_5y"],
                "latest_income_growth": signals["latest_income_growth"],
                "net_margin": signals["net_margin"],
                "profit_consistency": signals["profit_consistency"],
                "debt_cash": signals["debt_cash"],
                "pe_ratio": signals["pe_ratio"],
                "market_cap_to_income": signals["market_cap_to_income"],
                "risk_flags": scored["risk_flags"],
            }
        )
    return sorted(result, key=lambda x: (-x["multibagger_screen_score"], x["symbol"] or ""))
