"""Command-line entry point for the ASET research engine."""

from __future__ import annotations

import argparse
import json

from .analytics import annualized_volatility, maximum_drawdown, simple_return
from .providers import make_fixture_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-research",
        description="Run deterministic ASET research analytics.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Run the built-in deterministic demo.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "demo":
        provider = make_fixture_provider()
        observations = provider.get_prices("ASET", provider.get_prices("ASET", __import__("datetime").date(2024, 1, 1), __import__("datetime").date(2024, 1, 5))[0].trading_date, __import__("datetime").date(2024, 1, 5))
        output = {
            "symbol": "ASET",
            "simple_return": simple_return(observations).value,
            "annualized_volatility": annualized_volatility(observations).value,
            "maximum_drawdown": maximum_drawdown(observations).value,
            "observation_count": len(observations),
        }
        print(json.dumps(output, indent=2))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
