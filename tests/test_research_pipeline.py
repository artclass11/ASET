from stock_analyzer.research_pipeline import MultibaggerPipelineConfig, run_multibagger_pipeline


def test_pipeline_stages_and_ranks_without_network(monkeypatch) -> None:
    monkeypatch.setattr(
        "stock_analyzer.research_pipeline.fetch_universe_financedatabase",
        lambda **kwargs: {
            "status": "ok",
            "source": "FinanceDatabase",
            "record_count": 2,
            "records": [{"symbol": "AAA"}, {"symbol": "BBB"}],
        },
    )
    monkeypatch.setattr(
        "stock_analyzer.research_pipeline.screen_yfinance_equities",
        lambda **kwargs: {
            "status": "ok",
            "provider": "yfinance",
            "records": [
                {"symbol": "AAA", "revenue_growth_1y": 0.30},
                {"symbol": "BBB", "revenue_growth_1y": 0.05},
            ],
        },
    )

    def fake_fundamentals(symbols, max_workers=8, include_estimates=False):
        rows = []
        for symbol in symbols:
            rows.append(
                {
                    "status": "ok",
                    "provider": "yfinance",
                    "symbol": symbol,
                    "profile": {
                        "name": symbol,
                        "country": "US",
                        "exchange": "NASDAQ",
                        "sector": "Technology",
                        "industry": "Software",
                        "market_cap": 1_000_000_000,
                    },
                    "income_statement": [
                        {"period": "2025-12-31", "TotalRevenue": 300.0, "NetIncome": 60.0 if symbol == "AAA" else 20.0},
                        {"period": "2024-12-31", "TotalRevenue": 250.0, "NetIncome": 48.0 if symbol == "AAA" else 19.0},
                        {"period": "2023-12-31", "TotalRevenue": 205.0, "NetIncome": 38.0 if symbol == "AAA" else 18.0},
                        {"period": "2022-12-31", "TotalRevenue": 165.0, "NetIncome": 29.0 if symbol == "AAA" else 17.0},
                        {"period": "2021-12-31", "TotalRevenue": 130.0, "NetIncome": 22.0 if symbol == "AAA" else 16.0},
                    ],
                    "balance_sheet": [
                        {"TotalDebt": 100.0, "CashCashEquivalentsAndShortTermInvestments": 500.0}
                    ],
                    "valuation": [],
                    "cash_flow": [],
                    "observed_at": "2026-10-04T00:00:00Z",
                }
            )
        return {
            "status": "ok",
            "provider": "yfinance",
            "requested_symbols": len(symbols),
            "succeeded_symbols": len(rows),
            "failed_symbols": 0,
            "results": rows,
            "failures": [],
        }

    monkeypatch.setattr(
        "stock_analyzer.research_pipeline.fetch_yfinance_fundamentals_many",
        fake_fundamentals,
    )

    result = run_multibagger_pipeline(
        config=MultibaggerPipelineConfig(
            region="global",
            universe_limit=2,
            fast_screen_limit=2,
            fundamentals_limit=2,
            top_k=2,
            max_workers=1,
        )
    )

    assert result["status"] == "ok"
    assert [row["symbol"] for row in result["candidates"]] == ["AAA", "BBB"]
    assert len(result["audit"]["stages"]) >= 3
    assert result["audit"]["stages"][0]["name"] == "universe_discovery"
    assert result["audit"]["stages"][1]["name"] == "fast_numeric_screen"
    assert result["audit"]["stages"][2]["name"] == "deep_fundamentals"


def test_pipeline_never_promotes_incomplete_history(monkeypatch) -> None:
    monkeypatch.setattr(
        "stock_analyzer.research_pipeline.fetch_universe_financedatabase",
        lambda **kwargs: {
            "status": "ok",
            "source": "FinanceDatabase",
            "record_count": 1,
            "records": [{"symbol": "SHORT"}],
        },
    )
    monkeypatch.setattr(
        "stock_analyzer.research_pipeline.screen_yfinance_equities",
        lambda **kwargs: {
            "status": "ok",
            "provider": "yfinance",
            "records": [{"symbol": "SHORT", "revenue_growth_1y": 0.80}],
        },
    )
    monkeypatch.setattr(
        "stock_analyzer.research_pipeline.fetch_yfinance_fundamentals_many",
        lambda *args, **kwargs: {
            "status": "ok",
            "results": [
                {
                    "status": "ok",
                    "provider": "yfinance",
                    "symbol": "SHORT",
                    "profile": {
                        "name": "SHORT",
                        "country": "US",
                        "exchange": "NASDAQ",
                        "sector": "Technology",
                        "industry": "Software",
                        "market_cap": 1_000_000_000,
                    },
                    "income_statement": [
                        {"period": "2025-12-31", "TotalRevenue": 300.0, "NetIncome": 60.0},
                        {"period": "2024-12-31", "TotalRevenue": 250.0, "NetIncome": 48.0},
                    ],
                    "balance_sheet": [],
                    "valuation": [],
                    "cash_flow": [],
                    "observed_at": "2026-10-04T00:00:00Z",
                }
            ],
            "succeeded_symbols": 1,
            "failed_symbols": 0,
            "failures": [],
        },
    )

    result = run_multibagger_pipeline(
        config=MultibaggerPipelineConfig(
            region="global",
            universe_limit=1,
            fast_screen_limit=1,
            fundamentals_limit=1,
            top_k=1,
            max_workers=1,
        )
    )
    candidate = result["candidates"][0]
    assert candidate["tier"] != "A - immediate research candidate"
    assert candidate["signals"]["research_ready"] is False
