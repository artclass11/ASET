"""CLI for automatic ASET dataset/source routing."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from .data_router import all_source_health, filter_finance_database, route_workflow
from .research_pipeline import MultibaggerPipelineConfig, run_multibagger_pipeline
from .source_adapters import (
    choose_backtest_engine,
    fetch_sec_company_filing,
    fetch_yfinance_prices,
)


def _json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASET automatic dataset router and source manager")
    sub = parser.add_subparsers(dest="command", required=True)

    route = sub.add_parser("route", help="choose the best available source projects")
    route.add_argument("task")
    route.add_argument("--region", default="global")
    route.add_argument("--scale", choices=("small", "medium", "large", "xlarge"), default="medium")
    route.add_argument(
        "--stage",
        choices=("development", "discover", "screen", "deep_dive", "verification", "macro", "backtest", "optimization"),
        default="screen",
    )

    sub.add_parser("sources", help="show source and engine health")

    universe = sub.add_parser("universe", help="filter the FinanceDatabase equity universe")
    universe.add_argument("--country")
    universe.add_argument("--exchange")
    universe.add_argument("--sector")
    universe.add_argument("--industry")
    universe.add_argument("--market-cap", action="append", dest="market_cap_categories", help="market-cap bucket; repeatable")
    universe.add_argument("--include-delisted", action="store_true")
    universe.add_argument("--all-listings", action="store_true")
    universe.add_argument("--limit", type=int, default=10_000)

    prices = sub.add_parser("prices", help="download batch historical prices through yfinance")
    prices.add_argument("symbols", nargs="+")
    prices.add_argument("--start")
    prices.add_argument("--end")
    prices.add_argument("--period", default="1y")

    filing = sub.add_parser("filing", help="retrieve a current SEC filing through EdgarTools")
    filing.add_argument("symbol")
    filing.add_argument("--form", default="10-K")

    pipeline = sub.add_parser("pipeline", help="run the staged automatic multibagger research pipeline")
    pipeline.add_argument("--region", default="global")
    pipeline.add_argument("--universe-limit", type=int, default=20_000)
    pipeline.add_argument("--fast-screen-limit", type=int, default=1_000)
    pipeline.add_argument("--fundamentals-limit", type=int, default=25)
    pipeline.add_argument("--top-k", type=int, default=20)
    pipeline.add_argument("--max-workers", type=int, default=8)
    pipeline.add_argument("--verify-us-filings", type=int, default=0)

    backtest = sub.add_parser("backtest-engine", help="choose an installed quant engine")
    backtest.add_argument("--prefer", choices=("auto", "vectorbt", "backtrader", "lean"), default="auto")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "route":
        _json(route_workflow(args.task, region=args.region, scale=args.scale, stage=args.stage))
        return 0

    if args.command == "sources":
        _json(all_source_health())
        _json({"backtest": choose_backtest_engine()})
        return 0

    if args.command == "universe":
        result = filter_finance_database(
            country=args.country,
            exchange=args.exchange,
            sector=args.sector,
            industry=args.industry,
            market_cap_categories=args.market_cap_categories,
            only_primary_listing=not args.all_listings,
            include_delisted=args.include_delisted,
            limit=args.limit,
        )
        _json(result)
        return 0 if result.get("status") == "ok" else 2

    if args.command == "prices":
        start = date.fromisoformat(args.start) if args.start else None
        end = date.fromisoformat(args.end) if args.end else None
        _json(fetch_yfinance_prices(args.symbols, start=start, end=end, period=args.period))
        return 0

    if args.command == "filing":
        _json(fetch_sec_company_filing(args.symbol, form=args.form))
        return 0

    if args.command == "pipeline":
        config = MultibaggerPipelineConfig(
            region=args.region,
            universe_limit=max(1, min(args.universe_limit, 100_000)),
            fast_screen_limit=max(1, min(args.fast_screen_limit, 2_500)),
            fundamentals_limit=max(1, min(args.fundamentals_limit, 100)),
            top_k=max(1, min(args.top_k, 100)),
            max_workers=max(1, min(args.max_workers, 16)),
            verify_us_filings=max(0, min(args.verify_us_filings, 10)),
        )
        _json(run_multibagger_pipeline(config=config))
        return 0

    if args.command == "backtest-engine":
        _json(choose_backtest_engine(args.prefer))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
