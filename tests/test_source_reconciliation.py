from __future__ import annotations

from source_reconciliation import reconcile_rows


def test_reconcile_rows_marks_cross_provider_match() -> None:
    rows = [
        {
            "symbol": "ABC",
            "company": "Example Co",
            "provider": "Alpha Vantage",
            "fundamentals": {
                "revenue": 1000,
                "net_income": 100,
                "market_cap": 2000,
                "debt": 100,
                "cash": 200,
            },
        }
    ]
    yahoo = {
        "ABC": {
            "provider": "Yahoo Finance via yfinance",
            "fields": {
                "revenue": 1000,
                "net_income": 101,
                "market_cap": 1990,
                "debt": 100,
                "cash": 202,
            },
        }
    }

    result = reconcile_rows(rows, yahoo)[0]

    assert result["verification"]["status"] == "cross_checked"
    assert result["verification"]["grade"] == "A"
    assert result["verification"]["conflict_fields"] == 0
    assert result["field_checks"]["revenue"]["status"] == "match"


def test_reconcile_rows_marks_material_conflict() -> None:
    rows = [
        {
            "symbol": "XYZ",
            "fundamentals": {
                "revenue": 1000,
                "net_income": 100,
                "market_cap": 2000,
                "debt": 100,
                "cash": 200,
            },
        }
    ]
    yahoo = {
        "XYZ": {
            "provider": "Yahoo Finance via yfinance",
            "fields": {
                "revenue": 1400,
                "net_income": 100,
                "market_cap": 2000,
                "debt": 100,
                "cash": 200,
            },
        }
    }

    result = reconcile_rows(rows, yahoo)[0]

    assert result["verification"]["status"] == "conflict"
    assert result["verification"]["grade"] == "D"
    assert result["verification"]["conflict_fields"] == 1
    assert result["field_checks"]["revenue"]["status"] == "conflict"


def test_reconcile_rows_keeps_single_source_explicit() -> None:
    rows = [
        {
            "symbol": "ONLY",
            "fundamentals": {"revenue": 1000},
        }
    ]

    result = reconcile_rows(rows, {})[0]

    assert result["verification"]["status"] == "single_source"
    assert result["verification"]["grade"] == "C"
    assert result["verification"]["primary_source_verification"] == "pending"
