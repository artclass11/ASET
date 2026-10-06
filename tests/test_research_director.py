import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "live-signaldesk"))

from research_agent import ResearchAgentConfig, ResearchDirector  # noqa: E402


def row(symbol: str, score_input: float, completeness: float) -> dict:
    return {
        "symbol": symbol,
        "company": f"{symbol} plc",
        "country": "US",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "fundamentals": {
            "revenue": 300.0,
            "net_income": 60.0,
            "income_growth": 0.20,
            "net_margin": 0.20,
            "average_5y_net_income": 45.0,
            "debt": 30.0,
            "cash": 100.0,
            "debt_cash": 0.30,
            "market_cap": 1500.0,
            "market_cap_to_income": 25.0,
            "pe_ratio": 25.0,
        },
        "income_history": [
            {"fiscal_date": "2025-12-31", "revenue": 300.0, "net_income": 60.0},
            {"fiscal_date": "2024-12-31", "revenue": 250.0, "net_income": 48.0},
            {"fiscal_date": "2023-12-31", "revenue": 205.0, "net_income": 38.0},
            {"fiscal_date": "2022-12-31", "revenue": 165.0, "net_income": 29.0},
            {"fiscal_date": "2021-12-31", "revenue": 130.0, "net_income": 22.0},
        ],
        "flags": [f"fixture-{score_input}"],
        "provider": "fixture",
        "fetched_at": "2026-10-05T00:00:00Z",
        "freshness": "fixture",
        "quality": completeness,
    }


def test_large_universe_is_partitioned_and_deduplicated():
    async def fake_get(path: str):
        if path == "/health":
            return {"status": "healthy"}
        return {"provider": "fixture", "mode": "test"}

    async def fake_fetch(symbols, entitlement):
        return [row(symbol, 1.0, 80.0) for symbol in symbols], []

    def fake_normalize(symbols):
        return list(dict.fromkeys(s.strip().upper() for s in symbols))

    agent = ResearchDirector(
        ResearchAgentConfig(
            batch_size=2,
            shortlist_per_batch=2,
            default_top_k=4,
            default_deep_diligence_k=2,
            enable_cross_provider_check=False,
        ),
        api_base="test://signaldesk",
        api_get_fn=fake_get,
        fetch_many_fn=fake_fetch,
        normalize_symbols_fn=fake_normalize,
    )

    result = asyncio.run(
        agent.run(["a", "b", "c", "d", "d"], top_k=4, deep_diligence_k=2)
    )

    assert result["universe"]["requested"] == 4
    assert result["universe"]["batch_count"] == 2
    assert len(result["shortlist"]) == 4
    assert len(result["deep_diligence_queue"]) == 2
    assert result["shortlist"][0]["provenance"]["provider"] == "fixture"
    assert result["export_dataset"]["schema_version"] == "aset_research_workbook.v1"
    assert len(result["export_dataset"]["records"]) == 4


def test_low_evidence_candidates_are_gated():
    async def fake_get(path: str):
        return {"status": "healthy"} if path == "/health" else {"provider": "fixture"}

    async def fake_fetch(symbols, entitlement):
        item = row(symbols[0], 1.0, 20.0)
        item["fundamentals"].update(
            {
                "revenue": None,
                "net_income": None,
                "average_5y_net_income": None,
                "debt": None,
                "cash": None,
                "market_cap": None,
            }
        )
        return [item], []

    def fake_normalize(symbols):
        return list(dict.fromkeys(s.strip().upper() for s in symbols))

    agent = ResearchDirector(
        ResearchAgentConfig(
            batch_size=10,
            default_top_k=5,
            default_deep_diligence_k=2,
            min_evidence_completeness=60.0,
            enable_cross_provider_check=False,
        ),
        api_get_fn=fake_get,
        fetch_many_fn=fake_fetch,
        normalize_symbols_fn=fake_normalize,
    )

    result = asyncio.run(agent.run(["ABC"], top_k=5, deep_diligence_k=2))

    assert result["deep_diligence_queue"] == []
    assert result["evidence_rejections"]
    assert result["evidence_rejections"][0]["status"] == "evidence gap"


def test_preflight_failure_is_degraded_but_does_not_crash():
    async def fake_get(path: str):
        raise RuntimeError("provider unavailable")

    async def fake_fetch(symbols, entitlement):
        return [row(symbols[0], 1.0, 80.0)], []

    def fake_normalize(symbols):
        return list(dict.fromkeys(s.strip().upper() for s in symbols))

    agent = ResearchDirector(
        api_get_fn=fake_get,
        fetch_many_fn=fake_fetch,
        normalize_symbols_fn=fake_normalize,
    )

    result = asyncio.run(agent.run(["ABC"], top_k=1, deep_diligence_k=1))

    assert result["preflight"]["healthy"] is False
    assert result["stages"][0]["status"] == "degraded"
    assert result["deep_diligence_queue"]


def test_config_rejects_invalid_batch_size():
    with pytest.raises(ValueError):
        ResearchDirector(ResearchAgentConfig(batch_size=0))
