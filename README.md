# ASET

## Open research infrastructure for public equities

ASET is an open-source foundation for multi-provider stock research, screening, deterministic analytics and quantitative backtesting. The project is designed around reproducibility, provider provenance and clean interfaces that can scale from local research to production services.

[![CI](https://github.com/artclass11/ASET/actions/workflows/signaldesk.yml/badge.svg)](https://github.com/artclass11/ASET/actions/workflows/signaldesk.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-white.svg)](LICENSE)

### What is inside

| Layer | Purpose |
| --- | --- |
| Research engine | Python domain models, providers, API and deterministic analytics |
| SignalDesk | Productized fundamentals-to-research workflow |
| Quant roadmap | Backtrader, vectorbt and LEAN integration direction |
| Deployment | API-first architecture for caching, jobs and production services |

### SignalDesk

**Import → validate → calculate → inspect → export.**

Open the interactive local dashboard:

[Launch SignalDesk](products/signaldesk/index.html)

Free core includes CSV validation, net margin, income growth, average supplied net income, debt/cash, market-cap-to-income proxy, flags and JSON/Markdown output.

Commercial Pro can be licensed separately for live data adapters, scheduled refresh, PDF/HTML reports, saved workspaces, API/team deployment, custom integrations and enterprise support.

**Buy / license:** [Instagram @amormagics](https://www.instagram.com/amormagics/) · [Direct message](https://ig.me/m/amormagics)

See [docs/product.md](docs/product.md) for the commercial workflow and scope.

## Research engine

### Python

Requirements: Python 3.11+.

```bash
python -m pip install -e ./stock_analyzer
stock-research demo
```

### API

```bash
uvicorn stock_analyzer.api:app --host 127.0.0.1 --port 8000
```

The included API currently uses a deterministic fixture provider for development. Production data-provider wiring should be configured explicitly.

## Data integrity

ASET preserves provider provenance and quality metadata in its normalized research model. Coverage and definitions vary by provider. Material figures should be validated against authoritative filings and source data before use.

## Security

Never commit API keys, access tokens, cloud credentials, private datasets or customer information. See [SECURITY.md](SECURITY.md).

## Contributing

Focused pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the issue templates and the pull-request checklist.

## Scope

ASET is research and analytics software. It does not submit brokerage orders, provide custody, or execute transactions.

## License

MIT. See [LICENSE](LICENSE). Third-party dependencies keep their own licenses.