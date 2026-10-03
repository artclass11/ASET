#!/usr/bin/env python3
"""ASET SignalDesk: small, dependency-free financial research brief generator.

The core intentionally works from user-supplied CSV data so it can run offline.
It does not fetch prices, place orders, or provide investment advice.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, cast

REQUIRED = {"ticker", "company", "revenue", "net_income", "market_cap", "debt", "cash"}
HISTORY = [f"net_income_y{i}" for i in range(1, 6)]


def num(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        x = float(str(value).replace(",", "").strip())
        return x if math.isfinite(x) else None
    except ValueError:
        return None


def growth(current: float | None, prior: float | None) -> float | None:
    if current is None or prior in (None, 0):
        return None
    return (current / prior) - 1.0


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def money(x: float | None) -> str:
    return "n/a" if x is None else f"{x:,.2f}"


def analyze(row: dict[str, str]) -> dict[str, Any]:
    revenue = num(row.get("revenue"))
    income = num(row.get("net_income"))
    market_cap = num(row.get("market_cap"))
    debt = num(row.get("debt"))
    cash = num(row.get("cash"))

    historical: list[float] = [cast(float, value) for key in HISTORY if (value := num(row.get(key))) is not None]

    margin = income / revenue if income is not None and revenue not in (None, 0) else None
    debt_cash = debt / cash if debt is not None and cash not in (None, 0) else None
    earnings_multiple = market_cap / income if market_cap is not None and income not in (None, 0) else None

    prior = None
    if len(historical) >= 2:
        # y1 is assumed to be the latest supplied year and y5 the oldest.
        prior = historical[1]

    flags: list[str] = []
    if margin is not None and margin < 0:
        flags.append("negative-net-margin")
    if debt_cash is not None and debt_cash > 3:
        flags.append("high-debt-to-cash")
    if income is not None and income > 0 and earnings_multiple is not None and earnings_multiple > 60:
        flags.append("high-market-cap-to-earnings-proxy")
    latest_growth = growth(income, prior)
    if latest_growth is not None and latest_growth < 0:
        flags.append("latest-vs-prior-net-income-down")

    return {
        "ticker": row.get("ticker", "").strip(),
        "company": row.get("company", "").strip(),
        "financials": {
            "revenue": revenue,
            "net_income": income,
            "market_cap": market_cap,
            "debt": debt,
            "cash": cash,
            "net_margin": margin,
            "debt_to_cash": debt_cash,
            "market_cap_to_net_income": earnings_multiple,
            "average_net_income": average(historical),
            "latest_vs_prior_net_income_growth": latest_growth,
        },
        "flags": flags,
    }


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def render_markdown(items: list[dict[str, Any]]) -> str:
    lines = ["# SignalDesk Research Brief", "", f"Companies analyzed: **{len(items)}**", ""]
    for item in items:
        f = item["financials"]
        lines += [
            f"## {item['company']} ({item['ticker']})",
            "",
            f"- Revenue: {money(f['revenue'])}",
            f"- Net income: {money(f['net_income'])}",
            f"- Market cap: {money(f['market_cap'])}",
            f"- Net margin: {pct(f['net_margin'])}",
            f"- Debt / cash: {money(f['debt_to_cash'])}",
            f"- Market cap / net income proxy: {money(f['market_cap_to_net_income'])}",
            f"- Average supplied net income: {money(f['average_net_income'])}",
            f"- Latest vs prior net-income growth: {pct(f['latest_vs_prior_net_income_growth'])}",
            f"- Flags: {', '.join(item['flags']) if item['flags'] else 'none'}",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate analyst-style briefs from financial CSV data.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    try:
        rows = load_rows(args.csv_file)
        items = [analyze(row) for row in rows]
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
        return 2

    if args.format == "json":
        print(json.dumps({"companies": items}, indent=2))
    else:
        print(render_markdown(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
