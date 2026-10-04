# ASET

## Open research infrastructure for public equities

ASET is an open-source foundation for multi-provider stock research, screening, deterministic analytics and quantitative backtesting. The project is designed around reproducibility, provider provenance and clean interfaces that can scale from local research to production services.

[![CI](https://github.com/artclass11/ASET/actions/workflows/signaldesk.yml/badge.svg)](https://github.com/artclass11/ASET/actions/workflows/signaldesk.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-white.svg)](LICENSE)

## What is inside

| Layer | Purpose |
| --- | --- |
| Research engine | Python domain models, providers, API and deterministic analytics |
| SignalDesk | Productized fundamentals-to-research workflow |
| Quant roadmap | Backtrader, vectorbt and LEAN integration direction |
| Deployment | API-first architecture for caching, jobs and production services |

### SignalDesk

**Import → validate → calculate → inspect → export.**

Open the interactive local dashboard at [SignalDesk](products/signaldesk/index.html). The free core includes CSV validation, net margin, income growth, average supplied net income, debt/cash, market-cap-to-income proxy, flags and JSON/Markdown output.

Commercial Pro can be licensed separately for live data adapters, scheduled refresh, PDF/HTML reports, saved workspaces, API/team deployment, custom integrations and enterprise support. See [docs/product.md](docs/product.md) for the commercial workflow and scope.

## Research engine

### Python

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
stock-research
```

### API

The versioned read-only API exposes `/api/v1/health`, `/api/v1/readiness`, and bounded price queries at `/api/v1/securities/{symbol}/prices`. It uses a deterministic fixture provider for development; production provider wiring must be configured explicitly. See [docs/OPERATIONS.md](docs/OPERATIONS.md) for deployment and configuration guidance.

## Data integrity

ASET preserves provider provenance and quality metadata in its normalized research model. Coverage and definitions vary by provider. Material figures should be validated against authoritative filings and source data before use.

## Security

Never commit API keys, access tokens, cloud credentials, private datasets or customer information. See [SECURITY.md](SECURITY.md).

## Commercial readiness

The MIT license permits commercial use, but a sale also requires contributor-ownership confirmation, third-party dependency notices, provider-data rights review, and a written customer agreement. See [docs/COMMERCIAL_READINESS.md](docs/COMMERCIAL_READINESS.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). These documents are checklists, not legal advice.

## Assistant connectors

ASET includes a read-only MCP server that can connect the same research tools to ChatGPT, Claude, Manus, and other MCP-compatible hosts. See [docs/CONNECTORS.md](docs/CONNECTORS.md) for local stdio, remote HTTPS, and configuration examples.

## Contributing

Focused pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the issue templates and the pull-request checklist.

## Scope

ASET is research and analytics software. It does not submit brokerage orders, provide custody, or execute transactions.

## License

MIT. See [LICENSE](LICENSE). Third-party dependencies keep their own licenses.
