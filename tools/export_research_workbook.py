# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table

BLACK = "0B0B0D"
PANEL = "17171C"
WHITE = "F5F5F7"
MUTED = "A6A6AD"
ACCENT = "D7FF3F"
GRID = "33333A"
SOURCE_URL = "https://www.alphavantage.co/query"


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _style_title(ws, title: str, subtitle: str, end_col: int) -> None:
    ws.sheet_view.showGridLines = False
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=end_col)
    cell = ws.cell(1, 1, title)
    cell.font = Font(name="Aptos Display", size=20, bold=True, color=ACCENT)
    cell.fill = PatternFill("solid", fgColor=BLACK)
    ws.row_dimensions[1].height = 30
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=end_col)
    cell = ws.cell(2, 1, subtitle)
    cell.font = Font(name="Aptos", size=10, italic=True, color=MUTED)
    cell.fill = PatternFill("solid", fgColor=BLACK)
    ws.row_dimensions[2].height = 24


def _style_header(ws, row: int, columns: int) -> None:
    thin = Side(style="thin", color=GRID)
    for col in range(1, columns + 1):
        cell = ws.cell(row, col)
        cell.fill = PatternFill("solid", fgColor=PANEL)
        cell.font = Font(name="Aptos", size=10, bold=True, color=ACCENT)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=thin)


def _style_body(ws, start_row: int, end_row: int, columns: int) -> None:
    thin = Side(style="hair", color=GRID)
    for row in ws.iter_rows(min_row=start_row, max_row=end_row, min_col=1, max_col=columns):
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=BLACK)
            cell.font = Font(name="Aptos", size=9, color=WHITE)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=thin)


def _table(ws, ref: str, name: str) -> None:
    table = Table(displayName=name, ref=ref)
    ws.add_table(table)


def _widths(ws, widths: dict[int, float]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


def _source_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    seen: OrderedDict[str, list[Any]] = OrderedDict()
    for record in records:
        symbol = record.get("symbol")
        company = record.get("company") or symbol
        for source in record.get("sources") or []:
            provider = source.get("provider") or record.get("provider") or "ASET provider"
            function = source.get("function") or "research"
            fetched = source.get("fetched_at")
            key = f"{symbol}|{provider}|{function}|{fetched}"
            seen[key] = [
                key, symbol, company, provider, function,
                SOURCE_URL if provider == "Alpha Vantage" else "",
                fetched, source.get("freshness"), source.get("mode"),
                "provider_record", "2", "material financial data", "observed",
            ]
    return list(seen.values())


def _line_items(records: list[dict[str, Any]], history_key: str) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for record in records:
        symbol = record.get("symbol")
        company = record.get("company") or symbol
        currency = record.get("currency")
        meta = record.get("meta") or {}
        for period in record.get(history_key) or []:
            for key, value in period.items():
                if key == "fiscal_date":
                    continue
                numeric = _num(value)
                rows.append([
                    symbol, company, period.get("fiscal_date"), key,
                    numeric if numeric is not None else value, currency,
                    meta.get("provider") or "ASET provider",
                    meta.get("fetched_at"), meta.get("freshness"),
                ])
    return rows


def build_workbook(payload: dict[str, Any], output_path: str | Path) -> Path:
    export = payload.get("export_dataset") or {}
    records = list(export.get("records") or [])
    shortlist = list(payload.get("shortlist") or [])
    verification = list(export.get("verification") or payload.get("source_reconciliation") or [])
    verify_by_symbol = {
        str(item.get("symbol") or "").upper(): item.get("verification") or {}
        for item in verification
    }

    wb = Workbook()
    cover = wb.active
    cover.title = "Cover"
    _style_title(cover, "ASET / RESEARCH WORKBOOK", "Stable v1 • source-first research workbook", 8)
    cover_rows = [
        ("Run ID", payload.get("run_id")),
        ("Objective", payload.get("objective")),
        ("Universe Requested", (payload.get("universe") or {}).get("requested")),
        ("Universe Analyzed", (payload.get("universe") or {}).get("analyzed")),
        ("Candidates Exported", len(records)),
        ("Cross-checked", (payload.get("verification_summary") or {}).get("cross_checked")),
        ("Data policy", "Missing values remain blank; conflicts remain visible; no invented financials."),
        ("Contact", "Instagram @amormagics — https://www.instagram.com/amormagics/"),
    ]
    for row, (label, value) in enumerate(cover_rows, start=4):
        cover.cell(row, 1, label)
        cover.cell(row, 2, value)
        cover.cell(row, 1).fill = PatternFill("solid", fgColor=PANEL)
        cover.cell(row, 1).font = Font(name="Aptos", size=10, bold=True, color=ACCENT)
        cover.cell(row, 2).fill = PatternFill("solid", fgColor=BLACK)
        cover.cell(row, 2).font = Font(name="Aptos", size=10, color=WHITE)
        cover.cell(row, 2).alignment = Alignment(wrap_text=True, vertical="top")
    _widths(cover, {1: 26, 2: 100})
    cover.freeze_panes = "A4"

    rank = wb.create_sheet("Ranked_Screen")
    headers = [
        "Rank", "Ticker", "Issuer", "Country", "Exchange", "Sector", "Market Cap",
        "Score", "Tier", "Evidence %", "Revenue CAGR 5Y", "Net Income CAGR 5Y",
        "Net Margin", "Debt / Cash", "P/E", "Verification Grade", "Verification Status",
        "Primary Source", "Risk Flags", "Research Status",
    ]
    _style_title(
        rank,
        "RANKED SCREEN",
        "Research-priority ranking with separate evidence and verification",
        len(headers),
    )
    for col, name in enumerate(headers, 1):
        rank.cell(4, col, name)
    _style_header(rank, 4, len(headers))
    rank_end = max(5, 4 + len(shortlist))
    for row_no, candidate in enumerate(shortlist, start=5):
        symbol = str(candidate.get("symbol") or "").upper()
        signals = candidate.get("signals") or {}
        ver = verify_by_symbol.get(symbol, {})
        rank.cell(row_no, 1, f'=IF(B{row_no}="","",RANK.EQ(H{row_no},H5:H{rank_end},0))')
        values = [
            symbol, candidate.get("company") or symbol, candidate.get("country"),
            candidate.get("exchange"), candidate.get("sector"), candidate.get("market_cap"),
            candidate.get("score"), candidate.get("tier"), signals.get("evidence_completeness"),
            signals.get("revenue_cagr_5y"), signals.get("net_income_cagr_5y"),
            signals.get("net_margin"), signals.get("debt_cash"), signals.get("pe_ratio"),
            ver.get("grade"), ver.get("status"), ver.get("primary_source"),
            "; ".join(candidate.get("risk_flags") or []), candidate.get("status"),
        ]
        for col, value in enumerate(values, start=2):
            rank.cell(row_no, col, value)
        rank.cell(row_no, 7).number_format = '#,##0.0;[Red](#,##0.0);-'
        rank.cell(row_no, 8).number_format = '0.0;[Red](0.0);-'
        rank.cell(row_no, 10).number_format = '0.0;[Red](0.0);-'
        for col in (11, 12, 13):
            rank.cell(row_no, col).number_format = '0.0%;[Red](0.0%);-'
        for col in (13, 14, 15):
            rank.cell(row_no, col).number_format = '0.0x;[Red](0.0x);-'
    _style_body(rank, 5, rank_end, len(headers))
    if shortlist:
        _table(rank, f"A4:T{rank_end}", "RankedScreenTable")
    rank.freeze_panes = "A5"
    rank.auto_filter.ref = f"A4:T{rank_end}"
    _widths(
        rank,
        {
            1: 8, 2: 12, 3: 28, 4: 14, 5: 12, 6: 18, 7: 16, 8: 10, 9: 24, 10: 12,
            11: 16, 12: 18, 13: 12, 14: 12, 15: 10, 16: 18, 17: 24, 18: 28, 19: 44, 20: 18,
        },
    )

    fund = wb.create_sheet("Fundamentals")
    fheaders = [
        "Ticker", "Issuer", "Country", "Exchange", "Sector", "Industry", "Currency",
        "Freshness", "Revenue", "Net Income", "Average 5Y Net Income", "Net Margin",
        "Income Growth", "Operating Cash Flow", "Capital Expenditures", "Free Cash Flow",
        "Debt", "Cash", "Debt / Cash", "Market Cap", "Market Cap / Net Income",
        "P/E", "EPS", "Provider", "Fetched At",
    ]
    _style_title(fund, "FUNDAMENTALS", "Latest provider-reported values", len(fheaders))
    for col, name in enumerate(fheaders, 1):
        fund.cell(4, col, name)
    _style_header(fund, 4, len(fheaders))
    for row_no, record in enumerate(records, start=5):
        f = record.get("fundamentals") or {}
        meta = record.get("meta") or {}
        values = [
            record.get("symbol"), record.get("company"), record.get("country"), record.get("exchange"),
            record.get("sector"), record.get("industry"), record.get("currency"), meta.get("freshness"),
            f.get("revenue"), f.get("net_income"), f.get("average_5y_net_income"), f.get("net_margin"),
            f.get("income_growth"), f.get("operating_cash_flow"), f.get("capital_expenditures"),
            f.get("free_cash_flow"), f.get("debt"), f.get("cash"), f.get("debt_cash"), f.get("market_cap"),
            f.get("market_cap_to_income"), f.get("pe_ratio"), f.get("eps"),
            meta.get("provider"), meta.get("fetched_at"),
        ]
        for col, value in enumerate(values, 1):
            fund.cell(row_no, col, value)
        for col in (9, 10, 11, 14, 15, 16, 17, 18, 20):
            fund.cell(row_no, col).number_format = '#,##0.0;[Red](#,##0.0);-'
        for col in (12, 13):
            fund.cell(row_no, col).number_format = '0.0%;[Red](0.0%);-'
        for col in (19, 21, 22, 23):
            fund.cell(row_no, col).number_format = '0.0x;[Red](0.0x);-'
    fund_end = max(5, 4 + len(records))
    _style_body(fund, 5, fund_end, len(fheaders))
    if records:
        _table(fund, f"A4:Y{fund_end}", "FundamentalsTable")
    fund.freeze_panes = "A5"
    _widths(
        fund,
        {
            1: 12, 2: 28, 3: 14, 4: 12, 5: 18, 6: 24, 7: 10, 8: 28, 9: 15, 10: 15,
            11: 19, 12: 12, 13: 13, 14: 18, 15: 20, 16: 16, 17: 15, 18: 15, 19: 12,
            20: 17, 21: 22, 22: 10, 23: 10, 24: 24, 25: 24,
        },
    )

    income = wb.create_sheet("Income_5Y")
    iheaders = [
        "Ticker", "Issuer", "Currency", "FY1", "FY2", "FY3", "FY4", "FY5",
        "Revenue FY1", "Revenue FY2", "Revenue FY3", "Revenue FY4", "Revenue FY5",
        "Net Income FY1", "Net Income FY2", "Net Income FY3", "Net Income FY4", "Net Income FY5",
        "Revenue CAGR 5Y", "Net Income CAGR 5Y", "Average Net Income 5Y", "Observation Count", "Source",
    ]
    _style_title(
        income,
        "INCOME / 5-YEAR",
        "Five annual observations plus formula-derived metrics",
        len(iheaders),
    )
    for col, name in enumerate(iheaders, 1):
        income.cell(4, col, name)
    _style_header(income, 4, len(iheaders))
    for row_no, record in enumerate(records, start=5):
        hist = sorted(record.get("income_history") or [], key=lambda x: str(x.get("fiscal_date") or ""))[-5:]
        years = [x.get("fiscal_date") for x in hist]
        revenues = [x.get("revenue") for x in hist]
        incomes = [x.get("net_income") for x in hist]
        values = [record.get("symbol"), record.get("company"), record.get("currency"), *years, *revenues, *incomes]
        for col, value in enumerate(values, 1):
            income.cell(row_no, col, value)
        income.cell(row_no, 19, f'=IF(OR(I{row_no}="",M{row_no}="",I{row_no}<=0,M{row_no}<=0),"",(M{row_no}/I{row_no})^(1/(COUNT(I{row_no}:M{row_no})-1))-1)')
        income.cell(row_no, 20, f'=IF(OR(N{row_no}="",R{row_no}="",N{row_no}<=0,R{row_no}<=0),"",(R{row_no}/N{row_no})^(1/(COUNT(N{row_no}:R{row_no})-1))-1)')
        income.cell(row_no, 21, f'=IFERROR(AVERAGE(N{row_no}:R{row_no}),"")')
        income.cell(row_no, 22, f'=COUNT(N{row_no}:R{row_no})')
        income.cell(row_no, 23, f'=IF(A{row_no}="","","provider_record:"&A{row_no})')
        for col in range(9, 19):
            income.cell(row_no, col).number_format = '#,##0.0;[Red](#,##0.0);-'
        for col in (19, 20):
            income.cell(row_no, col).number_format = '0.0%;[Red](0.0%);-'
        income.cell(row_no, 21).number_format = '#,##0.0;[Red](#,##0.0);-'
    income_end = max(5, 4 + len(records))
    _style_body(income, 5, income_end, len(iheaders))
    if records:
        _table(income, f"A4:W{income_end}", "Income5YTable")
    income.freeze_panes = "A5"
    _widths(income, {1:12,2:28,3:10,4:13,5:13,6:13,7:13,8:13,9:16,10:16,11:16,12:16,13:16,14:18,15:18,16:18,17:18,18:18,19:18,20:20,21:20,22:16,23:24})

    balance = wb.create_sheet("Balance_Sheet_5Y")
    bheaders = ["Ticker", "Issuer", "Fiscal Date", "Line Item", "Value", "Currency", "Provider", "Fetched At", "Freshness"]
    _style_title(balance, "BALANCE SHEET / 5-YEAR", "All provider-returned annual balance-sheet line items", len(bheaders))
    for col, name in enumerate(bheaders, 1):
        balance.cell(4, col, name)
    _style_header(balance, 4, len(bheaders))
    rows = _line_items(records, "balance_sheet_history")
    for row_no, values in enumerate(rows, start=5):
        for col, value in enumerate(values, 1):
            balance.cell(row_no, col, value)
        balance.cell(row_no, 5).number_format = '#,##0.0;[Red](#,##0.0);-'
    balance_end = max(5, 4 + len(rows))
    _style_body(balance, 5, balance_end, len(bheaders))
    if rows:
        _table(balance, f"A4:I{balance_end}", "BalanceSheet5YTable")
    balance.freeze_panes = "A5"
    balance.auto_filter.ref = f"A4:I{balance_end}"
    _widths(balance, {1:12,2:28,3:14,4:44,5:18,6:10,7:24,8:24,9:28})

    cash = wb.create_sheet("Cash_Flow_5Y")
    cheaders = ["Ticker", "Issuer", "Fiscal Date", "Line Item", "Value", "Currency", "Provider", "Fetched At", "Freshness"]
    _style_title(cash, "CASH FLOW / 5-YEAR", "All provider-returned annual cash-flow line items", len(cheaders))
    for col, name in enumerate(cheaders, 1):
        cash.cell(4, col, name)
    _style_header(cash, 4, len(cheaders))
    rows = _line_items(records, "cash_flow_history")
    for row_no, values in enumerate(rows, start=5):
        for col, value in enumerate(values, 1):
            cash.cell(row_no, col, value)
        cash.cell(row_no, 5).number_format = '#,##0.0;[Red](#,##0.0);-'
    cash_end = max(5, 4 + len(rows))
    _style_body(cash, 5, cash_end, len(cheaders))
    if rows:
        _table(cash, f"A4:I{cash_end}", "CashFlow5YTable")
    cash.freeze_panes = "A5"
    cash.auto_filter.ref = f"A4:I{cash_end}"
    _widths(cash, {1:12,2:28,3:14,4:44,5:18,6:10,7:24,8:24,9:28})

    ver = wb.create_sheet("Verification")
    vheaders = ["Ticker", "Issuer", "Status", "Grade", "Primary Source", "Secondary Source", "Checked At", "Matched Fields", "Cross-checkable", "Conflicts", "Primary Filing Verification", "Note"]
    _style_title(ver, "SOURCE VERIFICATION", "Cross-provider reconciliation; primary filing verification remains separate", len(vheaders))
    for col, name in enumerate(vheaders, 1):
        ver.cell(4, col, name)
    _style_header(ver, 4, len(vheaders))
    for row_no, item in enumerate(verification, start=5):
        meta = item.get("verification") or {}
        values = [
            item.get("symbol"), item.get("company"), meta.get("status"), meta.get("grade"),
            meta.get("primary_source"), meta.get("secondary_source"), meta.get("checked_at"),
            meta.get("matched_fields"), meta.get("cross_checkable_fields"), meta.get("conflict_fields"),
            meta.get("primary_source_verification"), meta.get("material_claims_note"),
        ]
        for col, value in enumerate(values, 1):
            ver.cell(row_no, col, value)
    ver_end = max(5, 4 + len(verification))
    _style_body(ver, 5, ver_end, len(vheaders))
    if verification:
        _table(ver, f"A4:L{ver_end}", "VerificationTable")
    ver.freeze_panes = "A5"
    _widths(ver, {1:12,2:28,3:24,4:10,5:28,6:30,7:24,8:14,9:16,10:12,11:24,12:54})

    src = wb.create_sheet("Source_Manifest")
    sheaders = ["Source Ref", "Ticker", "Issuer", "Provider", "Function", "URL", "Retrieved At", "Freshness", "Mode", "Evidence Label", "Source Tier", "Claim Coverage", "Status"]
    _style_title(src, "SOURCE MANIFEST", "Traceability for exported provider records", len(sheaders))
    for col, name in enumerate(sheaders, 1):
        src.cell(4, col, name)
    _style_header(src, 4, len(sheaders))
    rows = _source_rows(records)
    for row_no, values in enumerate(rows, start=5):
        for col, value in enumerate(values, 1):
            src.cell(row_no, col, value)
    src_end = max(5, 4 + len(rows))
    _style_body(src, 5, src_end, len(sheaders))
    if rows:
        _table(src, f"A4:M{src_end}", "SourceManifestTable")
    src.freeze_panes = "A5"
    src.auto_filter.ref = f"A4:M{src_end}"
    _widths(src, {1:44,2:12,3:28,4:24,5:24,6:44,7:24,8:28,9:14,10:22,11:12,12:30,13:14})

    quality = wb.create_sheet("Data_Quality")
    qheaders = ["Ticker", "Issuer", "Evidence Score (%)", "Verification Grade", "Verification Status", "Risk Flags", "Data Gaps", "Research Status"]
    _style_title(quality, "DATA QUALITY", "Completeness is separate from attractiveness", len(qheaders))
    for col, name in enumerate(qheaders, 1):
        quality.cell(4, col, name)
    _style_header(quality, 4, len(qheaders))
    gaps = "; ".join(map(str, payload.get("data_gaps") or []))
    for row_no, candidate in enumerate(shortlist, start=5):
        symbol = str(candidate.get("symbol") or "").upper()
        signals = candidate.get("signals") or {}
        ver = verify_by_symbol.get(symbol, {})
        values = [
            symbol, candidate.get("company"), signals.get("evidence_completeness"),
            ver.get("grade"), ver.get("status"), "; ".join(candidate.get("risk_flags") or []),
            gaps, candidate.get("status"),
        ]
        for col, value in enumerate(values, 1):
            quality.cell(row_no, col, value)
        quality.cell(row_no, 3).number_format = '0.0;[Red](0.0);-'
    q_end = max(5, 4 + len(shortlist))
    _style_body(quality, 5, q_end, len(qheaders))
    if shortlist:
        _table(quality, f"A4:H{q_end}", "DataQualityTable")
    quality.freeze_panes = "A5"
    _widths(quality, {1:12,2:28,3:14,4:18,5:24,6:54,7:54,8:20})

    notes = wb.create_sheet("Notes")
    _style_title(notes, "NOTES / DEFINITIONS", "Stable workbook conventions", 3)
    note_rows = [
        ("Raw vs derived", "Provider-returned financials stay on raw tabs. CAGR, averages and ranks are formulas."),
        ("Missing data", "Blank means unavailable. Zero is only used when the source explicitly reports zero."),
        ("Units", "Keep provider-native units unless a documented conversion is included."),
        ("Verification", "A/B/C/D is source-confidence grading, not an investment rating."),
        ("Primary source", "Cross-provider agreement does not replace company filings or audited statements."),
        ("Ranking", "Rank is deterministic and intended for research prioritization."),
        ("Recalculation", "Open in Excel/Sheets for final formula recalculation if the host does not calculate cached formulas."),
    ]
    for row_no, (label, value) in enumerate(note_rows, start=4):
        notes.cell(row_no, 1, row_no - 3)
        notes.cell(row_no, 2, label)
        notes.cell(row_no, 3, value)
        notes.cell(row_no, 1).fill = PatternFill("solid", fgColor=PANEL)
        notes.cell(row_no, 1).font = Font(name="Aptos", bold=True, color=ACCENT)
        notes.cell(row_no, 2).fill = PatternFill("solid", fgColor=PANEL)
        notes.cell(row_no, 2).font = Font(name="Aptos", bold=True, color=WHITE)
        notes.cell(row_no, 3).fill = PatternFill("solid", fgColor=BLACK)
        notes.cell(row_no, 3).font = Font(name="Aptos", color=WHITE)
        notes.cell(row_no, 3).alignment = Alignment(wrap_text=True, vertical="top")
    _widths(notes, {1:8,2:24,3:100})

    for ws in wb.worksheets:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.tabColor = ACCENT

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a stable ASET workbook from a Research Director JSON payload.")
    parser.add_argument("payload_json", type=Path)
    parser.add_argument("--output", type=Path, default=Path("ASET_Research_Output.xlsx"))
    args = parser.parse_args()
    payload = json.loads(args.payload_json.read_text(encoding="utf-8"))
    print(build_workbook(payload, args.output))


if __name__ == "__main__":
    main()
