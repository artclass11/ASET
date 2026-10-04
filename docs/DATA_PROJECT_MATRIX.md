# ASET Data & Quant Project Matrix

ASET intentionally uses multiple open-source projects instead of forcing one library to do every job.

## Dataset projects

| Project | Role in ASET | Automatic stage | Notes |
| --- | --- | --- | --- |
| FinanceDatabase | Broad global instrument/universe metadata | Discover / filter | Metadata source, not live fundamentals |
| yfinance | Broad prices + native equity screener + shortlist fundamentals | Screen / enrich | Fast first-pass provider; validate material claims |
| AKShare | China/Hong Kong market-data route | Regional discovery / screen | API surface varies by upstream market source |
| EdgarTools | Structured U.S. SEC/XBRL verification | Deep dive / verify | Requires SEC identity |
| sec-edgar-downloader | Raw U.S. SEC filing ingestion fallback | Verify / local jobs | Controlled worker/ingestion flow |
| pandas-datareader | Macro/statistical series | Macro | Use for supported maintained data readers |
| OpenBB 5.x | Provider orchestration layer | Provider-specific routed stages | Core and provider extensions are installed separately |

## Quant engines

| Project | Role | Automatic choice | License note |
| --- | --- | --- | --- |
| VectorBT | Fast vectorized research | First when installed | Fair-code / Commons-Clause model; review before commercial redistribution |
| Backtrader | Event-driven backtesting | Fallback | GPLv3+ |
| QuantConnect LEAN | Larger algorithmic research / optimization | Fallback or explicit choice | Apache-2.0 |

## Routing rules

1. The router checks package availability and required credentials before selecting a source.
2. Broad metadata is gathered before expensive per-company enrichment.
3. Native bulk screeners are preferred for first-pass quantitative filtering.
4. Deep statements and filings are restricted to a bounded shortlist.
5. Provider-specific OpenBB packages are selected only when the concrete extension is installed.
6. Missing values are never replaced by model guesses.
7. ASET fixture data is development/test data only and cannot be selected for live research.
8. Software licenses do not grant rights to redistribute provider data; provider terms remain a separate deployment check.

## Validation

Run the source-health check and staged route before a large job. CI imports optional projects independently and runs the deterministic router/MCP tests.
