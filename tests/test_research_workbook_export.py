from pathlib import Path
import sys
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from export_research_workbook import build_workbook


def sample_payload():
    return {
        "run_id": "aset-test",
        "objective": "stability",
        "universe": {"requested": 2, "analyzed": 2},
        "verification_summary": {"cross_checked": 1},
        "data_gaps": [],
        "shortlist": [
            {
                "symbol": "TEST",
                "company": "Test Company",
                "country": "USA",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "score": 80.0,
                "tier": "A",
                "signals": {
                    "evidence_completeness": 100.0,
                    "revenue_cagr_5y": 0.10,
                    "net_income_cagr_5y": 0.12,
                    "net_margin": 0.20,
                    "debt_cash": 0.50,
                    "pe_ratio": 20.0,
                },
                "risk_flags": [],
                "status": "research candidate",
            }
        ],
        "export_dataset": {
            "records": [
                {
                    "symbol": "TEST",
                    "company": "Test Company",
                    "country": "USA",
                    "exchange": "NASDAQ",
                    "sector": "Technology",
                    "industry": "Software",
                    "currency": "USD",
                    "fundamentals": {
                        "revenue": 500,
                        "net_income": 100,
                        "average_5y_net_income": 80,
                        "net_margin": 0.20,
                        "income_growth": 0.12,
                        "operating_cash_flow": 120,
                        "capital_expenditures": 30,
                        "free_cash_flow": 90,
                        "debt": 50,
                        "cash": 100,
                        "debt_cash": 0.5,
                        "market_cap": 2000,
                        "market_cap_to_income": 20,
                        "pe_ratio": 20,
                        "eps": 5,
                    },
                    "meta": {
                        "provider": "Alpha Vantage",
                        "fetched_at": "2026-10-06T00:00:00+00:00",
                        "freshness": "provider",
                    },
                    "income_history": [
                        {"fiscal_date": "2022-12-31", "revenue": 300, "net_income": 50},
                        {"fiscal_date": "2023-12-31", "revenue": 350, "net_income": 60},
                        {"fiscal_date": "2024-12-31", "revenue": 400, "net_income": 72},
                        {"fiscal_date": "2025-12-31", "revenue": 450, "net_income": 85},
                        {"fiscal_date": "2026-12-31", "revenue": 500, "net_income": 100},
                    ],
                    "balance_sheet_history": [
                        {"fiscal_date": "2022-12-31", "cash": 60, "totalDebt": 40},
                        {"fiscal_date": "2023-12-31", "cash": 70, "totalDebt": 45},
                        {"fiscal_date": "2024-12-31", "cash": 80, "totalDebt": 45},
                        {"fiscal_date": "2025-12-31", "cash": 90, "totalDebt": 48},
                        {"fiscal_date": "2026-12-31", "cash": 100, "totalDebt": 50},
                    ],
                    "cash_flow_history": [
                        {"fiscal_date": "2022-12-31", "operatingCashflow": 70},
                        {"fiscal_date": "2023-12-31", "operatingCashflow": 80},
                        {"fiscal_date": "2024-12-31", "operatingCashflow": 95},
                        {"fiscal_date": "2025-12-31", "operatingCashflow": 105},
                        {"fiscal_date": "2026-12-31", "operatingCashflow": 120},
                    ],
                    "sources": [
                        {
                            "provider": "Alpha Vantage",
                            "function": "INCOME_STATEMENT",
                            "fetched_at": "2026-10-06T00:00:00+00:00",
                            "freshness": "provider",
                            "mode": "api-key",
                        }
                    ],
                }
            ],
            "verification": [
                {
                    "symbol": "TEST",
                    "company": "Test Company",
                    "verification": {
                        "status": "cross_checked",
                        "grade": "A",
                        "primary_source": "Alpha Vantage",
                        "secondary_source": "Yahoo Finance via yfinance",
                        "checked_at": "2026-10-06T00:01:00+00:00",
                        "matched_fields": 5,
                        "cross_checkable_fields": 5,
                        "conflict_fields": 0,
                        "primary_source_verification": "pending",
                        "material_claims_note": "Cross-check only",
                    },
                }
            ],
        },
    }


def test_workbook_contains_required_sheets_and_formulas(tmp_path):
    output = build_workbook(sample_payload(), tmp_path / "aset.xlsx")
    wb = openpyxl.load_workbook(output, data_only=False)
    assert wb.sheetnames == [
        "Cover",
        "Ranked_Screen",
        "Fundamentals",
        "Income_5Y",
        "Balance_Sheet_5Y",
        "Cash_Flow_5Y",
        "Verification",
        "Source_Manifest",
        "Data_Quality",
        "Notes",
    ]
    assert wb["Income_5Y"]["S5"].value.startswith("=IF(")
    assert wb["Income_5Y"]["T5"].value.startswith("=IF(")
    assert wb["Income_5Y"]["U5"].value.startswith("=IFERROR(")
    assert wb["Ranked_Screen"]["A5"].value.startswith("=IF(")
    assert wb["Balance_Sheet_5Y"]["E5"].value == 60
    assert wb["Verification"]["D5"].value == "A"
    assert wb["Cover"]["B10"].value is not None


def test_workbook_preserves_negative_values(tmp_path):
    payload = sample_payload()
    payload["export_dataset"]["records"][0]["cash_flow_history"][0]["capitalExpenditures"] = -20
    output = build_workbook(payload, tmp_path / "aset.xlsx")
    wb = openpyxl.load_workbook(output, data_only=False)
    assert wb["Cash_Flow_5Y"]["E5"].value == -20
