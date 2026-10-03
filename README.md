# ASET — Open Stock Research & Quantitative Engine

Open-source, multi-provider stock research, screening, analytics and quantitative backtesting platform.

## Providers
- yfinance
- FinanceDatabase
- AKShare
- pandas-datareader
- EdgarTools
- sec-edgar-downloader

## Quant engines
- Backtrader
- vectorbt
- QuantConnect LEAN

## Sellable product: ASET SignalDesk

**SignalDesk** is the first commercial-ready product layer in ASET: import financial fundamentals and generate a structured analyst-style research brief locally.

Free core:
- CSV validation
- growth calculations
- net margin
- debt-to-cash
- market-cap / net-income proxy
- average supplied net income
- Markdown or JSON reports

Commercial Pro:
- live-data provider adapters
- PDF/HTML report packs
- scheduled refresh
- saved watchlists
- API/team deployment
- custom branding and enterprise implementation

See [products/signaldesk/](products/signaldesk/) for the runnable core, sample data, commercial terms template and a minimal purchase page.

### Purchase

Current purchase/licensing is handled through **Instagram @amormagics**:

https://www.instagram.com/amormagics/

Direct message:
https://ig.me/m/amormagics

The GitHub repository is the product/demo surface; paid Pro delivery and support are handled separately. GitHub itself is not represented as the payment processor.

## Architecture direction

The project is designed for anonymous/public use, stateless API replicas, asynchronous research jobs, shared caching, persistent storage, analytical workloads and Kubernetes-based enterprise deployment.

## Status

ASET is under active development. The stock research engine remains the main platform, with SignalDesk providing a focused productized workflow.

## Data integrity

Provider coverage differs. The application preserves provider provenance and data-quality flags. Material financial figures should be validated against primary filings.

## License

MIT for the ASET project. External dependency licenses remain applicable to their respective projects.