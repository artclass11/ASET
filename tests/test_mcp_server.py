import asyncio
from datetime import date
from typing import cast

import pytest
from mcp.types import CallToolResult

pytest.importorskip("mcp")

from stock_analyzer.mcp_server import build_server  # noqa: E402


def test_mcp_exposes_read_only_research_tools() -> None:
    server = build_server()
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {
        "aset_get_security",
        "aset_get_prices",
        "aset_calculate_metrics",
    }

    result = cast(
        CallToolResult,
        asyncio.run(
            server.call_tool(
                "aset_get_prices",
                {"symbol": "ASET", "start": date(2024, 1, 1), "end": date(2024, 1, 5), "limit": 3},
            )
        ),
    )
    assert result.is_error is False
    assert result.structured_content["result"][0]["symbol"] == "ASET"
    assert len(result.structured_content["result"]) == 3


def test_mcp_metrics_include_provenance() -> None:
    server = build_server()
    result = cast(
        CallToolResult,
        asyncio.run(
            server.call_tool(
                "aset_calculate_metrics",
                {"symbol": "ASET", "start": date(2024, 1, 1), "end": date(2024, 1, 5)},
            )
        ),
    )
    assert result.is_error is False
    metrics = result.structured_content
    assert metrics["provider"] == "fixture"
    assert metrics["simple_return"]["provenance_refs"]


def test_mcp_rejects_unbounded_requests() -> None:
    server = build_server()
    with pytest.raises(Exception, match="limit"):
        asyncio.run(
            server.call_tool(
                "aset_get_prices",
                {"symbol": "ASET", "start": date(2024, 1, 1), "end": date(2024, 1, 5), "limit": 10_001},
            )
        )
