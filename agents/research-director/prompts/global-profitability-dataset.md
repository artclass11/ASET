# ASET Global 5-Year Profitability Dataset Protocol

Use this protocol whenever a user requests a worldwide top-N public-equity dataset ranked by five-year average net profit/net income.

## 1. Mission

Build an auditable research dataset, not a conversational estimate.

Primary objective:

Rank eligible listed companies by the arithmetic mean of five distinct completed annual net-income observations, normalized to USD using documented historical FX inputs.

Secondary analytics such as growth, margins, valuation, leverage, cash conversion and quality must never replace the primary ranking metric.

## 2. As-of and fiscal-period policy

Declare a data cutoff timestamp.

For every issuer, select the five latest distinct completed fiscal-year periods for which annual financial statements are actually available by the cutoff.

Do not use quarterly figures as annual figures, TTM/LTM as a fiscal year, forecasts, consensus estimates, partial current-year periods, or preliminary numbers when a final annual statement is available.

Record fiscal year label, fiscal period end, filing/release availability date when available, period length when available, and whether the value is restated.

A company with fewer than five valid annual net-income observations is retained in coverage but is NOT eligible for the complete five-year ranking.

## 3. Universe construction

Use a documented universe manifest.

The universe must identify issuer/legal entity, security identifier, ticker, exchange, country, share class, primary/canonical listing, ADR/GDR relationship where applicable, and active/inactive status.

Do not claim worldwide top 1000 unless the input universe has credible global coverage.

When a global exchange/security database is incomplete, explicitly state the coverage limitation.

Do not count multiple listings of the same issuer as separate companies.

Preserve excluded/duplicate listings in an Exceptions table.

## 4. Provider hierarchy

Use a source hierarchy and preserve the actual source used.

Preferred order for accounting facts:
1. company annual reports / regulatory filings;
2. SEC/EDGAR or equivalent regulator;
3. official exchange disclosures;
4. established financial-data provider;
5. Yahoo Finance/yfinance;
6. Alpha Vantage;
7. other documented providers.

The hierarchy is not permission to overwrite one provider with another.

Store all observed source values where cross-checking is performed.

## 5. Net-income definition

Declare one standardized primary ranking definition before calculation.

Preferred definition:
consolidated annual net income attributable to the parent/common shareholders, when consistently available.

If unavailable, use the closest provider-supported consolidated net-income line and record its exact source line-item name, definition, whether non-controlling interests are included/excluded, and any comparability warning.

Never silently mix incompatible net-income definitions.

Do not remove one-time items from the primary ranking.

Create a separate adjusted/normalized-profit analysis only when explicitly requested.

## 6. FX normalization

Because companies report in different currencies, every globally comparable ranking value must have a traceable FX conversion.

For each issuer-year store:
- reported currency;
- original amount;
- original unit;
- FX source;
- FX pair;
- FX rate;
- rate date or period convention;
- target currency USD;
- unit multiplier;
- converted USD amount.

Use a documented historical-period FX methodology.

Do not convert historical profit using today's FX rate unless the user explicitly asks for current-FX normalization.

If reliable FX is unavailable:
raw value stays in the dataset; USD value stays blank; issuer is excluded from the verified global USD ranking.

Never guess an FX rate.

## 7. Unit normalization

Record whether a source reports units, thousands, millions, billions, or another scale.

Keep original reported values and units.

Calculate normalized values with an explicit multiplier.

Never assume all providers use the same unit scale.

## 8. Primary ranking formula

For each eligible company:

five_year_average_net_income_usd = (Y1 + Y2 + Y3 + Y4 + Y5) / 5

where Y1...Y5 are the five selected completed annual normalized USD net-income observations.

Use the actual arithmetic mean.

Negative profit remains negative.

Do not replace negative numbers with zero.

Do not use an average of only the years that happen to be positive.

## 9. Completeness

Assign:
- 5/5 COMPLETE — eligible for primary ranking;
- 4/5 INCOMPLETE or lower — not eligible for primary ranking;
- CONFLICT — not eligible until reconciled;
- FX INCOMPLETE — not eligible for global USD ranking;
- IDENTITY CONFLICT — not eligible until resolved.

Also calculate observation count, years covered, raw completeness, FX completeness, and source completeness.

## 10. Restatements and accounting changes

Prefer the latest authoritative restated comparative figures when the source clearly identifies them as restated.

Do not combine an original historical value with a later restated value without recording the distinction.

Flag restatements, fiscal year-end changes, discontinued operations, major accounting-policy changes, and material classification changes.

## 11. Duplicates

Deduplicate at issuer level.

Treat these as potential duplicates:
- ordinary share + ADR;
- ordinary share + GDR;
- cross-listed shares;
- multiple exchange listings;
- multiple ticker aliases;
- multiple share classes where the user requested company-level ranking.

Keep all identifiers in a security-mapping table.

Never delete duplicate observations without retaining the reason.

## 12. Financial-sector and industry-specific debt rules

For companies where conventional net-debt/EBITDA is not meaningful, do not force the metric.

Examples may include banks, insurers, certain REITs, specialty finance, asset managers, and holding companies.

Use N/M where appropriate and apply sector-specific balance-sheet quality measures.

A low-debt screen is secondary to the primary profitability ranking.

## 13. Five-year statement capture

Collect all materially available annual line items.

Income statement:
Revenue, cost of revenue, gross profit, operating income, pretax income, tax, net income, attributable net income, EPS, shares and other provider-reported lines.

Balance sheet:
Cash, investments, receivables, inventory, current assets, PP&E, goodwill, intangibles, other assets, total assets, payables, short-term debt, long-term debt, lease liabilities, other liabilities, total liabilities, equity and non-controlling interest.

Cash flow:
Operating cash flow, capital expenditures, investing cash flow, financing cash flow, free cash flow when provider-supported, depreciation, amortization, stock compensation, dividends, borrowing/repayment, repurchases, acquisitions and material financing/investing lines.

Preserve provider line-item names.

## 14. Derived metrics

Calculate only from preserved source inputs.

At minimum calculate:
- five-year average net income;
- five-year median net income;
- minimum/maximum net income;
- revenue CAGR when mathematically valid;
- net-income CAGR when mathematically valid;
- average operating cash flow;
- average free cash flow;
- average net margin;
- ROE/ROA where meaningful;
- debt/equity;
- net debt;
- net debt/EBITDA where meaningful;
- cash conversion;
- current ratio / quick ratio where meaningful.

For mathematically invalid ratios/CAGRs, return blank or N/M with a reason.

## 15. Outlier and one-off analysis

Do not change the primary reported-profit ranking because of outliers.

Instead flag extraordinary gains/losses, asset-sale gains, litigation settlements, tax reversals, acquisition accounting, commodity spikes, pandemic-era distortions, restructuring, and major impairments.

Provide a separate normalized-profit commentary field when evidence supports it.

## 16. Validation

Run checks including:

Total Assets approximately equals Total Liabilities plus Total Equity, where provider data support the comparison.

Also check:
- duplicate fiscal dates;
- duplicate issuers;
- impossible dates;
- sign errors;
- unit mismatches;
- currency mismatches;
- debt consistency;
- cash-flow sign convention;
- missing periods;
- stale market data;
- source conflicts;
- unusual changes.

Never alter raw data to force a reconciliation.

## 17. Cross-source verification

For the highest-ranked companies and a documented sample of the broader universe, compare critical fields across independent sources.

Minimum fields:
- revenue;
- net income;
- total assets;
- debt;
- cash;
- operating cash flow;
- market capitalization.

Allowed statuses:
VERIFIED
PARTIALLY VERIFIED
PROVIDER ONLY
CONFLICT
UNAVAILABLE

A provider-to-provider match is not equivalent to audited filing verification.

For material business claims, use primary filings/IR/regulatory evidence.

## 18. Ranking coverage

For a request for top 99 or top 1000:

Do not screen only the first 99/1000 candidates.

Analyze the full declared universe first.

Batching is allowed for transport/rate limiting, but ranking must happen after merging the complete eligible population.

Batch-local multifactor scores may be used for triage only; they cannot determine the final profitability ranking.

## 19. Low-debt view

Produce two separate rankings.

Ranking A — Profitability:
Sort exclusively by five-year average annual net income USD.

Ranking B — Profitability + Balance-Sheet Quality:
Apply the stated low-debt rule after the complete profitability dataset exists.

Never modify Ranking A because of the low-debt filter.

## 20. Data-quality score

Create a transparent score separate from profitability.

Suggested components:
- 5Y completeness;
- source authority;
- independent verification;
- FX confidence;
- statement completeness;
- identity confidence;
- reconciliation quality;
- market-data freshness.

Never allow a quality score to turn missing information into an assumed value.

## 21. Required workbook structure

Create an institutional, minimal black Excel workbook with at least:
1. Cover
2. Universe
3. Ranked_Screen
4. Fundamentals
5. Income_5Y
6. Balance_Sheet_5Y
7. Cash_Flow_5Y
8. FX_Conversion
9. Verification
10. Source_Manifest
11. Data_Quality
12. Exceptions
13. Methodology
14. Notes

Ranked_Screen must include both raw ranking inputs and derived fields.

The detailed annual sheets must preserve raw provider observations.

## 22. Required Ranked_Screen fields

At minimum:
Rank
Issuer
Ticker
Security ID
Exchange
Country
Sector
Industry
Reporting Currency
FY1
FY2
FY3
FY4
FY5
Net Income FY1–FY5
FX FY1–FY5
Net Income USD FY1–FY5
5Y Average Net Income USD
5Y Median Net Income USD
Observation Count
Completeness
Market Cap
Enterprise Value
Cash
Total Debt
Net Debt
Debt/Equity
Net Debt/EBITDA or N/M
Operating Cash Flow
Free Cash Flow
Revenue CAGR
Net Income CAGR
Average Net Margin
ROE
ROA
Low-Debt Flag
Verification Status
Data-Quality Score
Primary Source
Source Count
Research Flags

## 23. Excel integrity

The workbook must:
- open successfully;
- contain all required sheets;
- use frozen headers;
- use filters/tables on data sheets;
- maintain formulas for derived values where safe;
- preserve negative values;
- leave unavailable data blank;
- avoid formula errors;
- avoid broken references;
- include reproducibility notes.

Do not use merged/decorative layouts that make filtering or machine reading difficult.

## 24. Failure behavior

If a provider fails, a source conflicts, FX is unavailable, or the universe cannot be fully analyzed:

do not manufacture a complete answer.

Return:
- status = PARTIAL or NOT VERIFIED;
- analyzed count;
- eligible count;
- excluded count;
- failure reasons;
- missing providers;
- unresolved conflicts;
- affected ranking coverage.

A smaller verified dataset is preferable to a larger fabricated dataset.

## 25. Reproducibility manifest

Record:
- generation timestamp UTC;
- data cutoff timestamp;
- software/version where available;
- provider names;
- endpoint/function names;
- request parameters where appropriate;
- universe source;
- FX source/method;
- ranking formula;
- filters;
- exclusions;
- verification methodology;
- dataset schema version.

The result must be reproducible from its exported inputs.

## 26. Final self-audit

Before reporting success, perform this checklist:
1. Is the universe actually global enough for the requested claim?
2. Were all requested securities analyzed rather than only a convenient shortlist?
3. Does every ranked company have five completed fiscal years?
4. Are the five values distinct fiscal periods?
5. Are all ranked profits normalized to USD through documented FX?
6. Are original values preserved?
7. Are negative values preserved?
8. Are duplicates resolved at issuer level?
9. Are restatements identified?
10. Are conflicts visible?
11. Are raw balance-sheet and cash-flow histories included?
12. Can every derived ranking number be recomputed?
13. Does the workbook open without errors?
14. Is the final rank based only on the requested metric?
15. Are all limitations disclosed?

If any answer is no, do not label the dataset fully verified.

## 27. Final response

Return a compact audit summary:
- requested universe;
- analyzed;
- eligible;
- ranked;
- incomplete;
- excluded;
- source coverage;
- FX coverage;
- verification coverage;
- conflict count;
- top ranked names;
- workbook path;
- schema version;
- data cutoff;
- known limitations.

Do not present the ranking as a forecast or investment recommendation.
