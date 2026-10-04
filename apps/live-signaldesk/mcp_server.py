from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from agent_engine import compare_payloads, rank_multibagger_candidates

SERVER_NAME = "ASET SignalDesk"
API_BASE = os.getenv("SIGNALDESK_API_BASE", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.getenv("SIGNALDESK_MCP_TIMEOUT_SECONDS", "30"))
AGENT_CONCURRENCY = max(1, min(int(os.getenv("ASET_AGENT_CONCURRENCY", "4")), 32))
AGENT_MAX_SYMBOLS = max(1, min(int(os.getenv("ASET_AGENT_MAX_SYMBOLS", "1000")), 5000))
_client: httpx.AsyncClient | None = None

mcp = MCPServer(
    SERVER_NAME,
    instructions=(
        "ASET SignalDesk is a read-only public-equity research tool. "
        "Use analyze_stock for provider-backed single-stock research and the batch "
        "screening tools for large universes. Never invent missing figures. Clearly "
        "distinguish provider freshness and demo-preview data from API-key-backed data. "
        "Multibagger radar identifies research candidates; it is not a prediction or "
        "investment recommendation. This server does not place trades."
    ),
)


async def api_get(path: str) -> dict[str, Any]:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=TIMEOUT,
            limits=httpx.Limits(
                max_connections=AGENT_CONCURRENCY * 2,
                max_keepalive_connections=AGENT_CONCURRENCY,
            ),
        )
    response = await _client.get(API_BASE + path, headers={"Accept": "application/json"})
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"SignalDesk returned non-JSON response ({response.status_code})") from exc
    if response.status_code >= 400:
        raise RuntimeError(str(payload.get("detail") or payload))
    return payload


def normalize_symbols(symbols: list[str]) -> list[str]:
    clean: list[str] = []
    seen: set[str] = set()
    for raw in symbols:
        normalized = str(raw).strip().upper()
        if not re.fullmatch(r"[A-Z0-9.-]{1,16}", normalized):
            continue
        if normalized not in seen:
            seen.add(normalized)
            clean.append(normalized)
    if not clean:
        raise ValueError("symbols must contain at least one valid ticker")
    if len(clean) > AGENT_MAX_SYMBOLS:
        raise ValueError(f"symbols exceeds ASET_AGENT_MAX_SYMBOLS={AGENT_MAX_SYMBOLS}")
    return clean


async def fetch_many(
    symbols: list[str],
    entitlement: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    clean = normalize_symbols(symbols)
    semaphore = asyncio.Semaphore(AGENT_CONCURRENCY)
    successes: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    async def worker(symbol: str) -> None:
        suffix = f"?entitlement={entitlement}" if entitlement else ""
        async with semaphore:
            try:
                successes.append(await api_get(f"/api/v1/research/{symbol}{suffix}"))
            except Exception as exc:
                failures.append({"symbol": symbol, "error": str(exc)})

    await asyncio.gather(*(worker(symbol) for symbol in clean))
    successes.sort(key=lambda item: item.get("symbol", ""))
    failures.sort(key=lambda item: item["symbol"])
    return successes, failures


@mcp.tool(
    title="Analyze stock",
    description=(
        "Analyze a ticker using ASET SignalDesk. Returns provider-backed quote, "
        "company identity, market cap, revenue, net income, five-year average "
        "net income, debt, cash, debt/cash, annual income history, transparent "
        "research flags, and source/freshness metadata."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def analyze_stock(symbol: str, entitlement: str = "") -> dict[str, Any]:
    """Analyze one public-company ticker."""
    normalized = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.-]{1,16}", normalized):
        raise ValueError("symbol must be 1-16 alphanumeric characters, dots, or hyphens")
    if entitlement not in ("", "realtime", "delayed"):
        raise ValueError("entitlement must be empty, realtime, or delayed")
    suffix = f"?entitlement={entitlement}" if entitlement else ""
    return await api_get(f"/api/v1/research/{normalized}{suffix}")


@mcp.tool(
    title="Check ASET SignalDesk",
    description="Check whether the configured ASET SignalDesk research API is healthy.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def check_signaldesk() -> dict[str, Any]:
    """Return service health and provider information."""
    return await api_get("/health")


@mcp.tool(
    title="Get SignalDesk configuration",
    description="Return non-secret SignalDesk configuration and provider availability.",
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def get_signaldesk_config() -> dict[str, Any]:
    """Return safe configuration metadata; API secrets are never returned."""
    return await api_get("/api/v1/config")


@mcp.tool(
    title="Screen stock universe",
    description=(
        "Run a bounded parallel quantitative screen across many tickers. Returns "
        "ranked research candidates, derived growth/quality/balance/valuation signals, "
        "data-completeness metadata, and failures. Best used before deep web or filing research."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def screen_universe(
    symbols: list[str],
    top_k: int = 25,
    entitlement: str = "",
) -> dict[str, Any]:
    """Screen up to the configured universe limit without fabricating data."""
    clean = normalize_symbols(symbols)
    if entitlement not in ("", "realtime", "delayed"):
        raise ValueError("entitlement must be empty, realtime, or delayed")
    top_k = max(1, min(int(top_k), 100))
    rows, failures = await fetch_many(clean, entitlement)
    candidates = rank_multibagger_candidates(rows, top_k=top_k)
    return {
        "screen": "ASET multi-factor public-equity research screen",
        "requested_symbols": len(clean),
        "analyzed_symbols": len(rows),
        "failed_symbols": len(failures),
        "failures": failures,
        "candidates": candidates,
        "next_step": (
            "Deep-research the highest-priority candidates with primary filings/IR "
            "and independent expectations/valuation checks."
        ),
    }


@mcp.tool(
    title="Compare stocks",
    description=(
        "Compare multiple provider-backed stocks on the same normalized fields, "
        "including five-year growth, profitability, balance-sheet and valuation signals."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def compare_stocks(
    symbols: list[str],
    entitlement: str = "",
) -> dict[str, Any]:
    """Return a compact normalized comparison set for research."""
    clean = normalize_symbols(symbols)
    if len(clean) > 100:
        raise ValueError("compare_stocks accepts at most 100 symbols per call")
    if entitlement not in ("", "realtime", "delayed"):
        raise ValueError("entitlement must be empty, realtime, or delayed")
    rows, failures = await fetch_many(clean, entitlement)
    return {
        "symbols": clean,
        "comparison": compare_payloads(rows),
        "failures": failures,
        "research_note": (
            "Comparison scores are screening aids, not intrinsic value estimates "
            "or investment recommendations."
        ),
    }


@mcp.tool(
    title="Multibagger radar",
    description=(
        "Find multi-year compounding candidates from a large ticker list. Scores "
        "growth, quality, balance sheet, valuation and evidence completeness, then "
        "labels candidates for deeper research instead of claiming certainty."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
)
async def multibagger_radar(
    symbols: list[str],
    top_k: int = 20,
    entitlement: str = "",
) -> dict[str, Any]:
    """Run the ASET multibagger candidate funnel across a ticker universe."""
    clean = normalize_symbols(symbols)
    if entitlement not in ("", "realtime", "delayed"):
        raise ValueError("entitlement must be empty, realtime, or delayed")
    top_k = max(1, min(int(top_k), 100))
    rows, failures = await fetch_many(clean, entitlement)
    candidates = rank_multibagger_candidates(rows, top_k=top_k)
    return {
        "objective": (
            "Identify research-worthy multi-year compounding candidates, "
            "not guaranteed multibaggers."
        ),
        "requested_symbols": len(clean),
        "analyzed_symbols": len(rows),
        "failed_symbols": len(failures),
        "candidates": candidates,
        "failures": failures,
        "adjudication_rules": [
            "Verify the economic driver with primary company or filing evidence.",
            "Test whether growth can persist without excessive dilution or leverage.",
            "Separate business quality from valuation and market expectations.",
            "Reject candidates where key evidence cannot be independently verified.",
        ],
    }


@mcp.prompt()
def research_prompt(
    symbol: str,
    focus: str = "fundamentals",
) -> str:
    """Create a reusable prompt for an equity research conversation."""
    return (
        f"Use ASET SignalDesk to research {symbol.upper()}. Focus on {focus}. "
        "Use only provider-returned values, call out missing data and freshness, "
        "and do not turn the result into a buy/sell recommendation."
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "stdio":
        mcp.run()
        return
    if transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8100")),
            streamable_http_path=os.getenv("MCP_PATH", "/mcp"),
            json_response=True,
            stateless_http=True,
            max_request_body_size=2 * 1024 * 1024,
        )
        return
    raise ValueError("MCP_TRANSPORT must be stdio or streamable-http")


if __name__ == "__main__":
    main()
