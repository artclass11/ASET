from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app as target


def payloads():
    return {
        "GLOBAL_QUOTE": {
            "Global Quote": {
                "05. price": "100",
                "09. change": "2",
                "10. change percent": "2.00%",
                "06. volume": "1000",
            }
        },
        "OVERVIEW": {
            "Name": "Test Company",
            "Exchange": "NASDAQ",
            "Country": "USA",
            "Currency": "USD",
            "MarketCapitalization": "1000000",
            "PERatio": "20",
            "EPS": "5",
        },
        "INCOME_STATEMENT": {
            "annualReports": [
                {"fiscalDateEnding": "2025-12-31", "totalRevenue": "500000", "netIncome": "100000"},
                {"fiscalDateEnding": "2024-12-31", "totalRevenue": "450000", "netIncome": "80000"},
                {"fiscalDateEnding": "2023-12-31", "totalRevenue": "400000", "netIncome": "70000"},
            ]
        },
        "BALANCE_SHEET": {
            "annualReports": [
                {
                    "fiscalDateEnding": "2025-12-31",
                    "shortTermDebt": "20000",
                    "longTermDebt": "30000",
                    "cashAndCashEquivalentsAtCarryingValue": "100000",
                }
            ]
        },
    }


@pytest.mark.asyncio
async def test_research_calculates_real_shape(monkeypatch):
    data = payloads()

    async def fake_av(function, symbol, entitlement=None, demo_allowed=False):
        return data[function], {
            "provider": "Alpha Vantage",
            "function": function,
            "fetched_at": "2026-01-01T00:00:00+00:00",
            "mode": "api-key",
            "freshness": "Default quote freshness / provider-dependent",
        }

    monkeypatch.setattr(target, "av", fake_av)
    result = await target.build_research("TEST", None)

    assert result["company"] == "Test Company"
    assert result["quote"]["price"] == 100
    assert result["fundamentals"]["net_margin"] == pytest.approx(0.2)
    assert result["fundamentals"]["debt"] == 50000
    assert result["fundamentals"]["cash"] == 100000
    assert result["fundamentals"]["debt_cash"] == pytest.approx(0.5)
    assert len(result["income_history"]) == 3


def test_invalid_symbol_rejected():
    assert not target.SYMBOL_RE.fullmatch("AAPL$")
    assert target.SYMBOL_RE.fullmatch("AAPL.US")


@pytest.mark.asyncio
async def test_missing_key_blocks_non_demo(monkeypatch):
    monkeypatch.setattr(target, "API_KEY", "")
    with pytest.raises(target.HTTPException) as exc:
        await target.av("OVERVIEW", "AAPL", None, True)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_demo_mode_is_restricted_to_ibm(monkeypatch):
    monkeypatch.setattr(target, "API_KEY", "")
    with pytest.raises(target.HTTPException):
        await target.av("OVERVIEW", "MSFT", None, True)
