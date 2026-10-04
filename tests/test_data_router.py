import os

from stock_analyzer.data_router import (
    DatasetKind,
    DatasetRequest,
    all_source_health,
    infer_kind,
    route,
    route_task,
)
from stock_analyzer.source_adapters import choose_backtest_engine, source_engine_status


def test_task_kind_inference() -> None:
    assert infer_kind("find a global stock universe") is DatasetKind.UNIVERSE
    assert infer_kind("download price history") is DatasetKind.PRICES
    assert infer_kind("read the latest 10-K filing") is DatasetKind.FILINGS
    assert infer_kind("run macro analysis") is DatasetKind.MACRO
    assert infer_kind("backtest 1000 parameter combinations") is DatasetKind.BACKTEST


def test_router_returns_auditable_plan() -> None:
    result = route(
        DatasetRequest(
            kind=DatasetKind.UNIVERSE,
            region="global",
            scale="large",
            stage="screen",
            requires_fresh=True,
        )
    )
    assert result["request"]["kind"] == "universe"
    assert "selected" in result
    assert "all_ranked_candidates" in result
    assert result["policy"]


def test_router_prefers_installed_provider(monkeypatch) -> None:
    def fake_installed(module: str | None) -> bool:
        return module in {"financedatabase"}

    monkeypatch.setattr("stock_analyzer.data_router.installed", fake_installed)
    result = route_task("screen a stock universe", region="global", scale="large", stage="screen")
    assert result["selected"][0]["source_id"] == "finance_database"


def test_source_health_has_all_expected_projects() -> None:
    ids = {row["source_id"] for row in all_source_health()}
    assert {"finance_database", "yfinance", "akshare", "edgartools", "openbb", "vectorbt", "backtrader", "lean"} <= ids


def test_no_fake_live_fallback() -> None:
    # This environment intentionally does not have optional provider packages.
    # The router must not silently substitute the ASET fixture for live research.
    monkeypatch_env = os.environ.copy()
    monkeypatch_env.pop("EDGAR_IDENTITY", None)
    rows = all_source_health()
    live_rows = [x for x in rows if x["source_id"] != "fixture"]
    assert all(x["status"] != "development_only" for x in live_rows)


def test_backtest_selection_is_explicit() -> None:
    result = choose_backtest_engine("auto")
    assert "selected" in result
    assert set(result["status"]) >= {"vectorbt", "backtrader", "lean_cli"}
    assert isinstance(source_engine_status(), dict)
