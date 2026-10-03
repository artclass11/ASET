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
The repository now includes a typed research domain, provenance-aware fixture provider, quantitative metrics, and a versioned read-only FastAPI service under `stock_analyzer/`.

## Quick start

```bash
python -m pip install -e '.[dev]'
stock-research
```

The API exposes `/api/v1/health`, `/api/v1/readiness`, and bounded price queries at `/api/v1/securities/{symbol}/prices`. See [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for configuration and deployment guidance.

## Data integrity
Provider coverage differs. The application preserves provider provenance and data-quality flags. Material financial figures should be validated against primary filings.

## License
MIT for the ASET project. External dependency licenses remain applicable to their respective projects.
