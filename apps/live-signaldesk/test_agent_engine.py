import unittest

from agent_engine import compare_payloads, rank_multibagger_candidates, score_candidate


def payload(
    symbol: str,
    revenue: float,
    income: float,
    income_growth: float,
    margin: float,
    pe: float,
    debt_cash: float,
    history: list[dict],
) -> dict:
    return {
        "symbol": symbol,
        "company": symbol + " plc",
        "country": "US",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "industry": "Software",
        "fundamentals": {
            "revenue": revenue,
            "net_income": income,
            "income_growth": income_growth,
            "net_margin": margin,
            "average_5y_net_income": income,
            "debt": debt_cash * 100,
            "cash": 100,
            "debt_cash": debt_cash,
            "market_cap": 1000,
            "market_cap_to_income": 1000 / income if income else None,
            "pe_ratio": pe,
        },
        "income_history": history,
        "flags": [],
    }


class AgentEngineTests(unittest.TestCase):
    def test_growth_quality_candidate_ranks_above_slow_business(self) -> None:
        strong = payload(
            "STRONG", 300, 60, 0.25, 0.20, 22, 0.3,
            [
                {"fiscal_date": "2025-12-31", "revenue": 300, "net_income": 60},
                {"fiscal_date": "2024-12-31", "revenue": 250, "net_income": 48},
                {"fiscal_date": "2023-12-31", "revenue": 205, "net_income": 38},
                {"fiscal_date": "2022-12-31", "revenue": 165, "net_income": 29},
                {"fiscal_date": "2021-12-31", "revenue": 130, "net_income": 22},
            ],
        )
        weak = payload(
            "WEAK", 220, 20, 0.03, 0.09, 80, 4.0,
            [
                {"fiscal_date": "2025-12-31", "revenue": 220, "net_income": 20},
                {"fiscal_date": "2024-12-31", "revenue": 214, "net_income": 19},
                {"fiscal_date": "2023-12-31", "revenue": 205, "net_income": 18},
                {"fiscal_date": "2022-12-31", "revenue": 197, "net_income": 17},
                {"fiscal_date": "2021-12-31", "revenue": 190, "net_income": 16},
            ],
        )

        ranked = rank_multibagger_candidates([weak, strong], top_k=2)

        self.assertEqual(ranked[0]["symbol"], "STRONG")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])
        self.assertIn("durable competitive advantage", ranked[0]["must_verify"][0])

    def test_missing_history_is_not_fabricated(self) -> None:
        row = payload("MISSING", 100, 10, 0.10, 0.10, 20, 0.5, [])
        scored = score_candidate(row)

        self.assertIsNone(scored["signals"]["revenue_cagr_5y"])
        self.assertIsNone(scored["signals"]["net_income_cagr_5y"])
        self.assertIn("five-year profit CAGR unavailable or not meaningful", scored["risk_flags"])

    def test_compare_output_is_sorted_and_compact(self) -> None:
        a = payload("A", 100, 10, 0.10, 0.10, 20, 0.5, [])
        b = payload("B", 100, 20, 0.15, 0.20, 15, 0.3, [])

        comparison = compare_payloads([a, b])

        self.assertEqual([x["symbol"] for x in comparison], ["B", "A"])
        self.assertIn("multibagger_screen_score", comparison[0])
        self.assertIn("risk_flags", comparison[0])


if __name__ == "__main__":
    unittest.main()
