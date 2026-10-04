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
    # Screening bands only; not a claim about future returns.
    return _clamp((cagr + 0.05) / 0.35 * 100.0)


def _valuation_penalty(pe: float | None, cap_income: float | None) -> float:
    value = pe if pe is not None and pe > 0 else cap_income if cap_income is not None and cap_income > 0 else None
    if value is None:
        return 0.0
    if value <= 15:
        return 8.0
    if value <= 25:
        return 3.0
    if value <= 40:
        return 0.0
    if value <= 60:
        return -5.0
    if value <= 100:
        return -12.0
    return -18.0


def _balance_score(debt_cash: float | None, debt: float | None, cash: float | None, sector: str | None) -> float | None:
    # Debt/cash is not comparable across financial institutions. Do not penalize
    # banks/insurers merely because their capital structure naturally carries debt.
    sector_lower = (sector or "").lower()
    if any(word in sector_lower for word in ("financial", "bank", "insurance")):
        return None
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
        return 90.0 if cash > debt else 35.0
    return None


def _cagr(start: float | None, end: float | None, periods: int) -> float | None:
    if start is None or end is None or periods <= 0 or start <= 0 or end <= 0:
        return None
    return (end / start) ** (1.0 / periods) - 1.0


def _history_metrics(row: dict[str, Any]) -> dict[str, Any]:
    history = row.get("income_history") or []
    ordered: list[dict[str, Any]] = []

    for item in history[:5]:
        revenue = _number(item.get("revenue"))
        income = _number(item.get("net_income"))
        fiscal_date = item.get("fiscal_date")
        if fiscal_date and (revenue is not None or income is not None):
            ordered.append(
                {"fiscal_date": str(fiscal_date), "revenue": revenue, "net_income": income}
            )

    # SignalDesk returns newest first. Normalize to oldest -> newest.
    if len(ordered) >= 2 and ordered[0]["fiscal_date"] > ordered[-1]["fiscal_date"]:
        ordered.reverse()

    revenue_values = [item["revenue"] for item in ordered]
    income_values = [item["net_income"] for item in ordered]
    revenue_values = [x for x in revenue_values if x is not None]
    income_values = [x for x in income_values if x is not None]

    positive_profit_years = sum(x > 0 for x in income_values)
    profit_consistency = positive_profit_years / len(income_values) if income_values else None
    profit_turnaround = bool(income_values) and any(x <= 0 for x in income_values[:-1]) and income_values[-1] > 0

    margins = [
        income / revenue
        for income, revenue in zip(
            [item["net_income"] for item in ordered],
            [item["revenue"] for item in ordered],
        )
        if income is not None and revenue not in (None, 0)
    ]

    return {
        "observations": len(ordered),
        "complete_five_year_history": len(ordered) >= 5,
        "revenue_cagr": _cagr(
            revenue_values[0] if revenue_values else None,
            revenue_values[-1] if revenue_values else None,
            len(revenue_values) - 1,
        ),
        "net_income_cagr": _cagr(
            income_values[0] if income_values else None,
            income_values[-1] if income_values else None,
            len(income_values) - 1,
        ),
        "positive_profit_ratio": profit_consistency,
        "profit_turnaround": profit_turnaround,
        "margin_start": margins[0] if margins else None,
        "margin_end": margins[-1] if margins else None,
        "margin_delta": margins[-1] - margins[0] if len(margins) >= 2 else None,
    }


def score_candidate(row: dict[str, Any]) -> dict[str, Any]:
    fundamentals = row.get("fundamentals") or {}
    history = _history_metrics(row)

    sector = row.get("sector")
    net_margin = _number(fundamentals.get("net_margin"))
    income_growth = _number(fundamentals.get("income_growth"))
    pe_ratio = _number(fundamentals.get("pe_ratio"))
    cap_income = _number(fundamentals.get("market_cap_to_income"))
    debt_cash = _number(fundamentals.get("debt_cash"))
    debt = _number(fundamentals.get("debt"))
    cash = _number(fundamentals.get("cash"))
    market_cap = _number(fundamentals.get("market_cap"))

    growth_components = [
        score
        for score in (
            _growth_score(history["revenue_cagr"]),
            _growth_score(history["net_income_cagr"]),
            _growth_score(income_growth),
        )
        if score is not None
    ]
    growth_score = sum(growth_components) / len(growth_components) if growth_components else 0.0

    consistency_score = (
        history["positive_profit_ratio"] * 100.0
        if history["positive_profit_ratio"] is not None
        else 0.0
    )
    margin_score = (
        _clamp((net_margin + 0.05) / 0.35 * 100.0)
        if net_margin is not None
        else 0.0
    )
    margin_delta = history["margin_delta"]
    margin_trend_score = _clamp((margin_delta + 0.05) / 0.20 * 100.0) if margin_delta is not None else 0.0
    quality_score = 0.5 * consistency_score + 0.3 * margin_score + 0.2 * margin_trend_score

    balance = _balance_score(debt_cash, debt, cash, sector)
    balance_score = 60.0 if balance is None else balance

    size_score = 0.0
    if market_cap is not None:
        if market_cap < 2_000_000_000:
            size_score = 100.0
        elif market_cap < 10_000_000_000:
            size_score = 85.0
        elif market_cap < 50_000_000_000:
            size_score = 70.0
        elif market_cap < 200_000_000_000:
            size_score = 50.0
        else:
            size_score = 25.0

    evidence_fields = [
        fundamentals.get("revenue"),
        fundamentals.get("net_income"),
        fundamentals.get("average_5y_net_income"),
        market_cap,
        net_margin,
        history["revenue_cagr"],
        history["net_income_cagr"],
    ]
    evidence_completeness = sum(value is not None for value in evidence_fields) / len(evidence_fields) * 100.0

    raw_score = (
        growth_score * 0.45
        + quality_score * 0.20
        + balance_score * 0.10
        + size_score * 0.10
        + evidence_completeness * 0.05
        + 50.0 * 0.10
    )
    raw_score += _valuation_penalty(pe_ratio, cap_income)
    composite = _clamp(raw_score)

    risks = list(row.get("flags") or [])
    if history["observations"] < 5:
        risks.append("less than five annual observations available")
    if history["revenue_cagr"] is None:
        risks.append("five-year revenue CAGR unavailable or not meaningful")
    if history["net_income_cagr"] is None:
        risks.append("five-year profit CAGR unavailable or not meaningful")
    if history["profit_turnaround"]:
        risks.append("profit history includes a turnaround")
    if history["positive_profit_ratio"] is not None and history["positive_profit_ratio"] < 0.8:
        risks.append("profit consistency below 80%")
    if pe_ratio is not None and pe_ratio > 60:
        risks.append("valuation is high on provider P/E")
    if debt_cash is not None and debt_cash > 3:
        risks.append("high debt/cash")

    # Hard gates prevent incomplete or low-quality data from becoming an A-level result.
    research_ready = (
        history["complete_five_year_history"]
        and history["revenue_cagr"] is not None
        and history["net_income_cagr"] is not None
        and evidence_completeness >= 70.0
    )
    if not research_ready and composite >= 60.0:
        composite = min(composite, 59.99)

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
        "sector": sector,
        "industry": row.get("industry"),
        "market_cap": market_cap,
        "score": round(composite, 2),
        "tier": tier,
        "signals": {
            "revenue_cagr_5y": history["revenue_cagr"],
            "net_income_cagr_5y": history["net_income_cagr"],
            "latest_income_growth": income_growth,
            "net_margin": net_margin,
            "profit_consistency": history["positive_profit_ratio"],
            "margin_delta": history["margin_delta"],
            "debt_cash": debt_cash,
            "pe_ratio": pe_ratio,
            "market_cap_to_income": cap_income,
            "size_runway_score": size_score,
            "evidence_completeness": round(evidence_completeness, 2),
            "research_ready": research_ready,
        },
        "risk_flags": list(dict.fromkeys(risks)),
        "why_it_surfaced": (
            "Growth-first screen with quality, balance-sheet, size/runway and valuation checks."
            if tier in {"A - immediate research candidate", "B - watchlist / needs trigger"}
            else "Some quantitative signals surfaced the company, but evidence or quality gates remain."
        ),
        "must_verify": [
            "durable competitive advantage and reinvestment runway",
            "addressable market and proof the driver reaches reported revenue or cash flow",
            "ROIC/ROE, free-cash-flow conversion and incremental economics",
            "management capital allocation, dilution and share-count history",
            "valuation versus normalized earnings/free cash flow and market expectations",
            "customer/product concentration, cyclicality, governance and accounting quality",
            "dated catalysts and a clear thesis-killer",
        ],
        "status": "research candidate" if tier in {"A - immediate research candidate", "B - watchlist / needs trigger"} else "screen flag",
        "disclaimer": "Deterministic screening signal only; not a forecast, recommendation, or guarantee of multi-bagger returns.",
    }


def rank_multibagger_candidates(rows: Iterable[dict[str, Any]], top_k: int = 20) -> list[dict[str, Any]]:
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
                "size_runway_score": signals["size_runway_score"],
                "research_ready": signals["research_ready"],
                "risk_flags": scored["risk_flags"],
            }
        )
    return sorted(result, key=lambda x: (-x["multibagger_screen_score"], x["symbol"] or ""))
