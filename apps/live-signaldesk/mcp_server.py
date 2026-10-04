from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

SERVER_NAME = "ASET SignalDesk"
API_BASE = os.getenv("SIGNALDESK_API_BASE", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.getenv("SIGNALDESK_MCP_TIMEOUT_SECONDS", "30"))

mcp = MCPServer(
    SERVER_NAME,
    instructions=(
        "ASET SignalDesk is a read-only public-equity research tool. "
        "Use analyze_stock for provider-backed quote and fundamental research. "
        "Do not invent missing figures. Clearly distinguish provider freshness "
        "and demo-preview data from API-key-backed data. This server does not "
        "place trades or give investment advice."
    ),
)

async def api_get(path: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(API_BASE + path, headers={"Accept": "application/json"})
        payload = response.json()
        if response.status_code >= 400:
            raise RuntimeError(str(payload.get("detail") or payload))
        return payload

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
    """Analyze one public-company ticker. entitlement may be realtime or delayed."""
    normalized = symbol.strip().upper()
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

@mcp.prompt()
def research_prompt(symbol: str, focus: str = "fundamentals") -> str:
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
            host=os.getenv("MCP_HOST", "0.0.0.0"),
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
