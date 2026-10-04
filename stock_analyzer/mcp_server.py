"""Read-only Model Context Protocol server for ASET research data."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
from decimal import Decimal
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .analytics import annualized_volatility, maximum_drawdown, simple_return
from .config import Settings
from .providers import MarketDataProvider, make_fixture_provider


def _security_payload(security: Any) -> dict[str, Any]:
    return {
        "symbol": security.symbol,
        "name": security.name,
        "exchange": security.exchange,
        "currency": security.currency,
        "provenance": {
            "provider": security.provenance.provider,
            "source": security.provenance.source,
            "observed_at": security.provenance.observed_at.isoformat(),
            "as_of": security.provenance.as_of.isoformat(),
        },
    }


def _price_payload(item: Any) -> dict[str, Any]:
    return {
        "symbol": item.security.symbol,
        "trading_date": item.trading_date.isoformat(),
        "close": str(Decimal(item.close)),
        "currency": item.security.currency,
        "provider": item.provenance.provider,
        "source": item.provenance.source,
        "quality": item.provenance.quality.value,
    }


def _metric_payload(result: Any) -> dict[str, Any]:
    return {
        "metric": result.metric,
        "value": result.value,
        "start": result.start.isoformat(),
        "end": result.end.isoformat(),
        "observation_count": result.observation_count,
        "provenance_refs": list(result.provenance_refs),
    }


def build_server(provider: MarketDataProvider | None = None, settings: Settings | None = None) -> MCPServer:
    """Build an MCP server backed by an explicitly selected read-only provider."""
    selected_provider = provider or make_fixture_provider()
    selected_settings = settings or Settings.from_env()
    server = MCPServer(
        name="aset-research",
        title=selected_settings.app_name,
        description=(
            "Read-only ASET public-equity research tools. "
            "Results include provider provenance and are not investment advice."
        ),
        version="0.3.0",
        instructions=(
            "Use these tools for transparent research lookups only. "
            "Do not represent fixture data as live market data. "
            "Never place trades or infer personalized investment advice."
        ),
    )

    @server.tool(name="aset_get_security")
    def get_security(symbol: str) -> dict[str, Any]:
        """Get normalized security metadata and provenance for a ticker symbol."""
        if not 1 <= len(symbol.strip()) <= 16 or not symbol.replace(".", "").replace("-", "").isalnum():
            raise ToolError("symbol must be 1-16 alphanumeric characters, dots, or hyphens")
        return _security_payload(selected_provider.get_security(symbol.strip().upper()))

    @server.tool(name="aset_get_prices")
    def get_prices(symbol: str, start: date, end: date, limit: int = 500) -> list[dict[str, Any]]:
        """Get bounded historical closing prices with source and quality metadata."""
        if start > end:
            raise ToolError("start must not be after end")
        if limit < 1 or limit > selected_settings.max_price_points:
            raise ToolError(f"limit must be between 1 and {selected_settings.max_price_points}")
        observations = selected_provider.get_prices(symbol.strip().upper(), start, end)
        return [_price_payload(item) for item in observations[:limit]]

    @server.tool(name="aset_calculate_metrics")
    def calculate_metrics(symbol: str, start: date, end: date) -> dict[str, Any]:
        """Calculate transparent return, drawdown, and volatility metrics."""
        observations = selected_provider.get_prices(symbol.strip().upper(), start, end)
        return {
            "symbol": symbol.strip().upper(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "observations": len(observations),
            "simple_return": _metric_payload(simple_return(observations)),
            "maximum_drawdown": _metric_payload(maximum_drawdown(observations)),
            "annualized_volatility": _metric_payload(annualized_volatility(observations)),
            "provider": selected_provider.name,
        }

    return server


def main() -> None:
    """Run the ASET MCP server over stdio or Streamable HTTP."""
    parser = argparse.ArgumentParser(description="Run the read-only ASET MCP server")
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    server = build_server()
    if args.transport == "stdio":
        asyncio.run(server.run_stdio_async())
    else:
        asyncio.run(server.run_streamable_http_async(host=args.host, port=args.port, streamable_http_path="/mcp"))


if __name__ == "__main__":
    main()
