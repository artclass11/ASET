# ASET Research Engine

Python package for deterministic public-equity research analytics, automatic dataset routing, source-health checks and a small versioned FastAPI research API.

## Install

Core is intentionally lightweight:

~~~bash
python -m pip install -e .
~~~

Install only the data projects you need:

~~~bash
python -m pip install -e ".[universe,prices,china,sec,macro]"
~~~

Or install the full data stack:

~~~bash
python -m pip install -e ".[all]"
~~~

## Automatic dataset routing

ASET does not assume one provider is best for every job. The router evaluates dataset type, geography, scale, research stage, package availability and required credentials.

Typical selection:

| Task | Preferred project |
| --- | --- |
| Global equity universe / metadata filtering | FinanceDatabase |
| Broad price history | yfinance |
| China equity data | AKShare |
| U.S. filings / XBRL | EdgarTools |
| Raw SEC filing fallback | sec-edgar-downloader |
| Macro / statistical series | pandas-datareader |
| Multi-provider aggregation | OpenBB Platform |
| Fast vectorized backtests | VectorBT community edition |
| Event-driven backtests | Backtrader |
| Larger algorithmic research / optimization | LEAN |

These are routed sources/engines, not a claim that every project is authoritative for every field. A source-health check runs before selection, and missing data is never silently replaced by the fixture dataset.

## CLI

~~~bash
aset-dataset route "screen thousands of global growth stocks" --region global --scale xlarge --stage screen
aset-dataset sources
aset-dataset universe --country "United States" --sector Technology --limit 5000
aset-dataset prices AAPL MSFT NVDA --period 1y
aset-dataset filing AAPL --form 10-K
aset-dataset backtest-engine --prefer auto
~~~

## Research API

~~~bash
uvicorn stock_analyzer.api:app --host 127.0.0.1 --port 8000
~~~

The core API is read-only and keeps the provider boundary explicit. For live production data, use the routed provider services rather than the deterministic fixture.

## MCP

~~~bash
aset-mcp
~~~

The MCP surface exposes normalized research calculations plus:
- aset_route_dataset
- aset_source_health
- aset_filter_universe

These tools allow ChatGPT, Claude and Manus to select an appropriate open-source data project before fetching and filtering data.

## Design

Market observations stay tied to provenance, quality metadata, dates and currency. Provider adapters are lazy-loaded so unused projects do not slow startup or installation.
