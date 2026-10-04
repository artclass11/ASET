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
    assert {
        tool.name for tool in tools
    } >= {
        "aset_get_security",
        "aset_get_prices",
        "aset_calculate_metrics",
        "aset_route_dataset",
        "aset_source_health",
        "aset_filter_universe",
        "aset_yfinance_screen",
        "aset_openbb_coverage",
        "aset_auto_multibagger_screen",
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


def test_mcp_can_route_dataset_without_live_provider() -> None:
    server = build_server()
    result = cast(
        CallToolResult,
        asyncio.run(
            server.call_tool(
                "aset_route_dataset",
                {
                    "task": "screen thousands of global growth stocks",
                    "region": "global",
                    "scale": "xlarge",
                    "stage": "screen",
                },
            )
        ),
    )
    assert result.is_error is False
    payload = result.structured_content
    assert payload["request"]["kind"] == "universe"
    assert payload["request"]["scale"] == "xlarge"
    assert payload["policy"]


def test_mcp_auto_multibagger_tool_is_exposed() -> None:
    server = build_server()
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert "aset_auto_multibagger_screen" in names


def test_mcp_auto_multibagger_tool_uses_pipeline(monkeypatch) -> None:
    import stock_analyzer.research_pipeline as pipeline

    expected = {"status": "ok", "candidates": [{"symbol": "TEST"}]}
    monkeypatch.setattr(pipeline, "run_multibagger_pipeline", lambda **kwargs: expected)

    server = build_server()
    result = cast(
        CallToolResult,
        asyncio.run(
            server.call_tool(
                "aset_auto_multibagger_screen",
                {
                    "region": "global",
                    "top_k": 5,
                    "fundamentals_limit": 10,
                },
            )
        ),
    )
    assert result.is_error is False
    assert result.structured_content == expected


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
