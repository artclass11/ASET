from __future__ import annotations

# ruff: noqa: E501
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
OUT.mkdir(exist_ok=True)
XLSX = OUT / "ASET_Professional_Global_Equity_Research_Template.xlsx"
PDF = OUT / "ASET_Professional_Global_Equity_Research_Framework.pdf"

BLACK = "0B0B0D"
PANEL = "151519"
WHITE = "F4F4F5"
MUTED = "A6A6AD"
ACCENT = "D7FF3F"
BLUE = "69A7FF"
RED = "FF6B6B"
THIN = Side(style="thin", color="33333A")


def fill(cell, color=BLACK):
    cell.fill = PatternFill("solid", fgColor=color)
    cell.font = Font(name="Aptos", size=10, color=WHITE)
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    cell.border = Border(bottom=THIN)


def header(cell):
    fill(cell, PANEL)
    cell.font = Font(name="Aptos Display", size=10, bold=True, color=ACCENT)


def title(ws, text, subtitle):
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:H1")
    ws["A1"] = text
    ws["A1"].font = Font(name="Aptos Display", size=22, bold=True, color=ACCENT)
    ws["A1"].fill = PatternFill("solid", fgColor=BLACK)
    ws.merge_cells("A2:H2")
    ws["A2"] = subtitle
    ws["A2"].font = Font(name="Aptos", size=10, italic=True, color=MUTED)
    ws["A2"].fill = PatternFill("solid", fgColor=BLACK)
    ws.row_dimensions[1].height = 32
    ws.row_dimensions[2].height = 28
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None:
                cell.fill = PatternFill("solid", fgColor=BLACK)


def build_xlsx():
    wb = Workbook()
    cover = wb.active
    cover.title = "Cover"
    title(
        cover,
        "ASET / GLOBAL EQUITY RESEARCH",
        "Original, provenance-first workbook • blank until official data is loaded",
    )
    rows = [
        (4, "Purpose", "Deep company research and worldwide equity screening with auditable source mapping."),
        (5, "Data status", "TEMPLATE — no market figures or invented company data are included."),
        (6, "Source rule", "Only official sources in data/official_source_registry.csv and ASET provider records."),
        (
            7,
            "Scoring",
            "equity_v1: business 20%, financial quality 25%, valuation 20%, growth 15%, balance sheet 10%, risk 10%.",
        ),
        (
            8,
            "Coverage gate",
            "Do not rank a company with less than 60% weighted data coverage; label 60–<80% provisional.",
        ),
        (9, "Important", "Research only. No trade execution, personalized advice, or transaction capability."),
    ]
    for r, label, value in rows:
        cover[f"A{r}"] = label
        cover[f"B{r}"] = value
        header(cover[f"A{r}"])
        fill(cover[f"B{r}"])
    cover.column_dimensions["A"].width = 22
    cover.column_dimensions["B"].width = 105
    cover.freeze_panes = "A4"

    inp = wb.create_sheet("Screen_Input")
    title(inp, "SCREEN / INPUT", "Enter only verified values; blue text indicates user-entered source data")
    headers = [
        "Ticker",
        "Issuer",
        "Country",
        "Exchange",
        "Sector",
        "Currency",
        "As Of",
        "Source Ref",
        "Market Cap",
        "Revenue",
        "EBITDA Margin",
        "ROIC",
        "FCF Margin",
        "Net Debt / EBITDA",
        "Revenue CAGR 5Y",
        "P/E",
        "EV / EBITDA",
        "Liquidity Note",
        "Data Status",
        "Analyst Note",
    ]
    for c, h in enumerate(headers, 1):
        cell = inp.cell(4, c, h)
        header(cell)
    for r in range(5, 105):
        for c in range(1, len(headers) + 1):
            cell = inp.cell(r, c)
            fill(cell)
            if c in (9, 10):
                cell.number_format = "#,##0.0;(#,##0.0);-"
            if c in (11, 12, 13, 15):
                cell.number_format = "0.0%;(0.0%);-"
            if c in (14, 16, 17):
                cell.number_format = "0.0x;(0.0x);-"
            if c in (1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20):
                cell.font = Font(name="Aptos", size=10, color=BLUE)
    for c, w in enumerate([11, 24, 14, 12, 18, 10, 13, 16, 15, 15, 15, 12, 14, 16, 16, 10, 13, 24, 16, 34], 1):
        inp.column_dimensions[get_column_letter(c)].width = w
    inp.freeze_panes = "A5"
    inp.auto_filter.ref = "A4:T104"

    out = wb.create_sheet("Screen_Output")
    title(out, "SCREEN / OUTPUT", "Formula-driven ranking; blank or unverified records remain incomplete")
    out_headers = [
        "Ticker",
        "Issuer",
        "Eligibility",
        "Coverage",
        "Quality",
        "Growth",
        "Balance",
        "Valuation",
        "Risk",
        "Final Score",
        "Confidence",
        "Band",
        "Reason",
    ]
    for c, h in enumerate(out_headers, 1):
        header(out.cell(4, c, h))
    for r in range(5, 105):
        source = f"Screen_Input!H{r}"
        out.cell(r, 1, f'=IF({source}="","",Screen_Input!A{r})')
        out.cell(r, 2, f'=IF({source}="","",Screen_Input!B{r})')
        out.cell(r, 3, f'=IF({source}="","",IF(OR(Screen_Input!S{r}<>"verified",{source}=""),"INCOMPLETE","ELIGIBLE"))')
        out.cell(r, 4, f'=IF($A{r}="","",COUNT(Screen_Input!I{r}:Q{r})/9)')
        out.cell(r, 5, f'=IF($A{r}="","",IF(Screen_Input!K{r}="","",MIN(100,MAX(0,Screen_Input!K{r}*100))))')
        out.cell(r, 6, f'=IF($A{r}="","",IF(Screen_Input!O{r}="","",MIN(100,MAX(0,Screen_Input!O{r}*100))))')
        out.cell(r, 7, f'=IF($A{r}="","",IF(Screen_Input!N{r}="","",MIN(100,MAX(0,100-Screen_Input!N{r}*20))))')
        out.cell(r, 8, f'=IF($A{r}="","",IF(Screen_Input!P{r}="","",MIN(100,MAX(0,100-Screen_Input!P{r}*3))))')
        out.cell(r, 9, f'=IF($A{r}="","",IF(Screen_Input!S{r}<>"verified","",50))')
        out.cell(
            r,
            10,
            f'=IF(OR($A{r}="",$D{r}<0.6,$C{r}<>"ELIGIBLE"),"",ROUND(($E{r}*0.25+$F{r}*0.15+$G{r}*0.10+$H{r}*0.20+$I{r}*0.10+50*0.20),1))',
        )
        out.cell(r, 11, f'=IF($J{r}="","",ROUND($D{r}*100,0))')
        out.cell(
            r,
            12,
            f'=IF($J{r}="","",IF($J{r}>=85,"STRONG",IF($J{r}>=70,"POSITIVE",IF($J{r}>=55,"WATCH",IF($J{r}>=40,"WEAK","REJECT")))))',
        )
        out.cell(
            r,
            13,
            f'=IF($A{r}="","",IF($C{r}<>"ELIGIBLE","Needs verified source / data coverage",IF($D{r}<0.8,"Provisional coverage","Screened")))',
        )
        for c in range(1, 14):
            fill(out.cell(r, c))
        out.cell(r, 3).font = Font(name="Aptos", size=10, bold=True, color=RED)
        out.cell(r, 10).number_format = "0.0"
        out.cell(r, 11).number_format = "0%"
    for c, w in enumerate([11, 24, 14, 12, 12, 12, 12, 12, 12, 13, 13, 14, 34], 1):
        out.column_dimensions[get_column_letter(c)].width = w
    out.freeze_panes = "A5"
    out.auto_filter.ref = "A4:M104"

    card = wb.create_sheet("Research_Card")
    title(card, "RESEARCH / CARD", "Deep-dive structure for one issuer; duplicate the sheet per company")
    card_rows = [
        (4, "Entity Card", "Legal issuer / ticker / exchange / country / currency / fiscal year-end"),
        (5, "Research Question", "What must this analysis determine?"),
        (6, "Thesis", "One paragraph supported by source refs"),
        (7, "Refuting Evidence", "Evidence against the thesis"),
        (8, "Business & Moat", "Segments, customers, competition, pricing power, durability"),
        (9, "Financial Quality", "Growth, margins, ROIC, cash conversion, cyclicality"),
        (10, "Balance Sheet", "Net debt, maturities, liquidity, covenants, off-balance-sheet risks"),
        (11, "Valuation", "Base / bull / bear assumptions, methods, sensitivity and source refs"),
        (12, "Catalysts", "Observable events and expected timing"),
        (13, "Risks", "Risk, severity, likelihood, mitigation"),
        (14, "Monitoring", "Metrics and thresholds to monitor"),
        (15, "Invalidation", "Observable evidence that would invalidate the thesis"),
        (16, "Conclusion", "Research label, confidence, coverage and unresolved data gaps"),
    ]
    for r, label, prompt in card_rows:
        card[f"A{r}"] = label
        card[f"B{r}"] = prompt
        header(card[f"A{r}"])
        fill(card[f"B{r}"])
        card.row_dimensions[r].height = 34
    card.column_dimensions["A"].width = 24
    card.column_dimensions["B"].width = 105
    card.freeze_panes = "A4"

    src = wb.create_sheet("Source_Manifest")
    title(src, "SOURCE / MANIFEST", "Every material value must map to a source reference")
    src_headers = [
        "Source Ref",
        "Publisher",
        "Title",
        "URL or File",
        "Retrieved At",
        "Data As Of",
        "Publication Date",
        "Period",
        "Currency",
        "Unit",
        "Source Tier",
        "Original / Derived",
        "Claim Coverage",
        "Status",
        "Notes",
    ]
    for c, h in enumerate(src_headers, 1):
        header(src.cell(4, c, h))
    for r in range(5, 105):
        for c in range(1, len(src_headers) + 1):
            fill(src.cell(r, c))
            src.cell(r, c).font = Font(name="Aptos", size=10, color=BLUE)
    for c, w in enumerate([14, 24, 32, 42, 22, 16, 18, 12, 10, 14, 12, 16, 34, 16, 34], 1):
        src.column_dimensions[get_column_letter(c)].width = w
    src.freeze_panes = "A5"
    src.auto_filter.ref = "A4:O104"

    for ws in wb.worksheets:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.tabColor = ACCENT
    wb.save(XLSX)


def build_pdf():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BlackTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#D7FF3F"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BlackH",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#D7FF3F"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BlackBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#F4F4F5"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BlackSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#A6A6AD"),
            spaceAfter=4,
        )
    )
    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="ASET Professional Global Equity Research Framework",
        author="ASET",
    )
    story = [
        Paragraph("ASET / GLOBAL EQUITY RESEARCH", styles["BlackTitle"]),
        Paragraph("Professional worldwide equity screening and deep-research framework", styles["BlackBody"]),
        Spacer(1, 8),
    ]
    story += [
        Paragraph("STATUS", styles["BlackH"]),
        Paragraph(
            "ORIGINAL TEMPLATE — no market figures, rankings, or investment conclusions are fabricated in this document. Populate only from the official source registry and trace every material claim.",
            styles["BlackBody"],
        ),
    ]
    story += [
        Paragraph("1 / RESEARCH MANDATE", styles["BlackH"]),
        Paragraph(
            "Define universe, jurisdictions, exchanges, sector, market-cap and liquidity boundaries, valuation date, currency, fiscal basis, time horizon, and the decision question. Establish an entity card before analysis.",
            styles["BlackBody"],
        ),
    ]
    story += [
        Paragraph("2 / OFFICIAL-SOURCE POLICY", styles["BlackH"]),
        Paragraph(
            "Use regulator filings, exchange disclosures, issuer annual reports, official interim reports, official earnings materials, and approved ASET provider records. Preserve publisher, URL or file locator, publication date, retrieval time, period, currency, unit, source tier, and claim coverage. Search summaries and unverified aggregators are not evidence for key facts.",
            styles["BlackBody"],
        ),
    ]
    story += [Paragraph("3 / SCREENING PROFILE / equity_v1", styles["BlackH"])]
    data = [
        ["Dimension", "Weight", "Evidence focus"],
        ["Business & moat", "20%", "Segments, competition, pricing power, durability"],
        ["Financial quality", "25%", "Growth, margins, ROIC, cash conversion"],
        ["Valuation & expectations", "20%", "P/E, EV/EBITDA, scenarios, implied expectations"],
        ["Growth & catalysts", "15%", "Organic growth, runway, observable catalysts"],
        ["Balance sheet", "10%", "Net debt, maturities, liquidity, refinancing"],
        ["Governance & risk", "10%", "Disclosure, controls, concentration, tail risk"],
    ]
    table = Table(data, colWidths=[48 * mm, 20 * mm, 105 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#151519")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#D7FF3F")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#F4F4F5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#33333A")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story += [
        table,
        Paragraph(
            "Hard gates come before scores. Missing data is not a zero. Coverage below 60% is insufficient for a total ranking; 60–<80% is provisional.",
            styles["BlackSmall"],
        ),
    ]
    story += [
        Paragraph("4 / DEEP RESEARCH CARD", styles["BlackH"]),
        Paragraph(
            "Thesis • refuting evidence • business and moat • financial quality • balance sheet • valuation scenarios • catalysts • risks • monitoring metrics • invalidation conditions • source manifest • unresolved data gaps.",
            styles["BlackBody"],
        ),
    ]
    story += [
        Paragraph("5 / CONFIDENCE", styles["BlackH"]),
        Paragraph(
            "Confidence is evidence reliability, not attractiveness: 35% source quality + 30% data coverage + 20% cross-source consistency + 15% recency fit. Report the score and confidence separately.",
            styles["BlackBody"],
        ),
    ]
    story += [
        Paragraph("6 / DELIVERY CHECKLIST", styles["BlackH"]),
        Paragraph(
            "Validate entity identity, period consistency, currencies, units, reported versus adjusted basis, source mapping, formula integrity, missing fields, conflicts, and sensitivity. Export the companion workbook and preserve the original data artifacts.",
            styles["BlackBody"],
        ),
    ]
    story += [
        Spacer(1, 12),
        Paragraph("IMPORTANT NOTICE", styles["BlackH"]),
        Paragraph(
            "This framework is for research and analysis only. It does not guarantee future performance and does not constitute legal, tax, accounting, or personalized investment advice. ASET cannot place, modify, cancel, sign, transmit, or submit a financial transaction.",
            styles["BlackSmall"],
        ),
    ]

    def bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#0B0B0D"))
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=bg, onLaterPages=bg)


if __name__ == "__main__":
    build_xlsx()
    build_pdf()
    print(XLSX)
    print(PDF)
