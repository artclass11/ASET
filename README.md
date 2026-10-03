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

## Architecture direction
The project is designed for anonymous/public use, stateless API replicas, asynchronous research jobs, shared caching, persistent storage, analytical workloads and Kubernetes-based enterprise deployment.

## Status
Initial ASET repository bootstrap. See the application package under `stock_analyzer/`.

## Data integrity
Provider coverage differs. The application preserves provider provenance and data-quality flags. Material financial figures should be validated against primary filings.

## License
MIT for the ASET project. External dependency licenses remain applicable to their respective projects.
