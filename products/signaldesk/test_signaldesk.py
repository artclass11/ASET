import csv
import io
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from signaldesk import analyze, load_rows, render_markdown


def test_analyze():
    row = {
        "ticker": "TEST",
        "company": "Test Co",
        "revenue": "100",
        "net_income": "20",
        "market_cap": "400",
        "debt": "50",
        "cash": "100",
        "net_income_y1": "20",
        "net_income_y2": "10",
        "net_income_y3": "",
        "net_income_y4": "",
        "net_income_y5": "",
    }
    result = analyze(row)
    assert result["financials"]["net_margin"] == 0.2
    assert result["financials"]["debt_to_cash"] == 0.5
    assert result["financials"]["market_cap_to_net_income"] == 20
    assert result["financials"]["average_net_income"] == 15
    assert "latest_vs_prior_net_income_growth" in result["financials"]


def test_sample_data():
    path = Path(__file__).parent / "sample_data" / "companies.csv"
    rows = load_rows(path)
    assert len(rows) == 3
    assert "revenue" in rows[0]
    md = render_markdown([analyze(row) for row in rows])
    assert "# SignalDesk Research Brief" in md
    assert "Nova Systems" in md


if __name__ == "__main__":
    test_analyze()
    test_sample_data()
    print("All SignalDesk tests passed")
