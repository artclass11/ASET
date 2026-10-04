from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

API_BASE = os.getenv("SIGNALDESK_API_BASE", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.getenv("SIGNALDESK_MCP_TIMEOUT_SECONDS", "30"))

mcp = MCPServer(
    "ASET SignalDesk",
    instructions=(
        "Read-only public-equity research. Use provider-returned values only; "
        "never invent missing figures. Preserve provider and freshness metadata. "
        "Do not place trades or give investment advice."
    ),
)

async def api_get(path: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(API_BASE + path, headers={"Accept": "application/json"})
        data = response.json()
        if response.status_code >= 400:
            raise RuntimeError(str(data.get("detail") or data))
        return data

@mcp.tool(title="Analyze stock", annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True))
async def analyze_stock(symbol: str, entitlement: str = "") -> dict[str, Any]:
    """Analyze one ticker using ASET SignalDesk."""
    symbol = symbol.strip().upper()
    if entitlement not in ("", "realtime", "delayed"):
        raise ValueError("entitlement must be empty, realtime, or delayed")
    suffix = f"?entitlement={entitlement}" if entitlement else ""
    return await api_get(f"/api/v1/research/{symbol}{suffix}")

@mcp.tool(title="Check ASET SignalDesk", annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True))
async def check_signaldesk() -> dict[str, Any]:
    """Return ASET API health."""
    return await api_get("/health")

@mcp.tool(title="Get SignalDesk configuration", annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True))
async def get_signaldesk_config() -> dict[str, Any]:
    """Return safe ASET configuration metadata."""
    return await api_get("/api/v1/config")

@mcp.prompt()
def research_prompt(symbol: str, focus: str = "fundamentals") -> str:
    """Create an ASET-focused research prompt."""
    return (
        f"Use ASET SignalDesk to research {symbol.upper()} with a focus on {focus}. "
        "Use only provider-returned values, report data freshness and missing fields, "
        "and do not turn the result into a trade recommendation."
    )

if __name__ == "__main__":
    mcp.run()
