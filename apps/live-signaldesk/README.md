# ASET SignalDesk Live

Self-hostable live financial research web app powered by the Alpha Vantage API.

## Highlights
- Real provider-backed quote and fundamental data
- Server-side API key handling
- Explicit provider, endpoint, fetch-time and freshness metadata
- Deterministic research calculations
- Transparent data-quality flags
- Minimal black responsive UI
- Docker + Docker Compose deployment
- Compatible with self-hosted Coolify
- MCP-native batch screening for multi-stock agents
- Deterministic multibagger candidate ranking

## Data provider

The app uses Alpha Vantage's official query API for GLOBAL_QUOTE, OVERVIEW, INCOME_STATEMENT, and BALANCE_SHEET.

Alpha Vantage documents that the default quote endpoint may be end-of-day, while realtime and 15-minute delayed US market-data access depends on the appropriate entitlement. See: https://www.alphavantage.co/documentation/

When ALPHAVANTAGE_API_KEY is not configured, only IBM uses the clearly labeled Alpha Vantage demo preview. No synthetic stock values are generated.

## Local Docker test

Copy the environment example to .env and set your API key.

~~~bash
cp .env.example .env
docker compose up -d --build
~~~

Open http://localhost:8000.

## Self-hosted deployment

This directory is intentionally portable. It contains a standard Dockerfile and Docker Compose definition, so it can run on a Linux VPS, dedicated server, home lab or an open-source deployment platform.

### Coolify

Coolify supports Git repositories using Dockerfile or Docker Compose deployments and can run workloads on infrastructure you control.

Repository: https://github.com/artclass11/ASET

Application root: apps/live-signaldesk

For the Windows desktop client, allow these origins (or your exact controlled origins) with SIGNALDESK_CORS_ORIGINS:

http://tauri.localhost,http://localhost:1420,http://127.0.0.1:1420

Set secret:

ALPHAVANTAGE_API_KEY

For MCP batch research, configure:

- ASET_AGENT_CONCURRENCY: provider-safe parallelism; default 4.
- ASET_AGENT_MAX_SYMBOLS: maximum symbols accepted per screening call; default 1000.
- SIGNALDESK_MCP_TIMEOUT_SECONDS: per-request timeout; default 30 seconds.

Expose port 8000 for the API. Expose the MCP service only through a controlled HTTPS reverse proxy with authentication and rate limiting.

Coolify: https://coolify.io/
Deployment guide: https://coolify.io/docs/applications/choose-deployment-method

## API

GET /health

GET /api/v1/config

GET /api/v1/research/IBM

GET /api/v1/research/AAPL?entitlement=delayed

GET /api/v1/research/MSFT?entitlement=realtime

The batch agent layer is exposed through MCP tools rather than a public bulk API.

## MCP agent tools

- analyze_stock: one-stock provider-backed research
- screen_universe: parallel multi-stock quantitative screening
- compare_stocks: normalized side-by-side comparison
- multibagger_radar: multi-year compounding candidate funnel
- check_signaldesk: health
- get_signaldesk_config: safe non-secret configuration

## Large-universe reality

The agent interface can accept large symbol lists and partition them into batches, but provider throughput and licensing still determine how many symbols can be refreshed in practice.

The current implementation is Alpha Vantage-backed. For reliable thousands-of-symbol production coverage, configure a market-data provider/tier whose licensing, symbol coverage, request rate and redistribution rights match the deployment. Do not infer that a free/demo quota can support an enterprise scan.

## Security

Never commit .env or API keys. The browser talks only to the SignalDesk server; the Alpha Vantage credential stays in the server environment.

The container uses a read-only filesystem with a temporary /tmp mount and no-new-privileges.

For a public MCP endpoint, add authentication, rate limits, request quotas and observability at the reverse-proxy/API layer before exposing it to untrusted users.

## Commercial Pro

The public app is the live demonstration surface. Commercial licensing can add additional providers, report generation, scheduled refresh, authentication, team workspaces and deployment support.

Purchase/support: https://www.instagram.com/amormagics/

Direct message: https://ig.me/m/amormagics/

## Disclaimer

Market data may be delayed or entitlement-dependent. Validate material figures against authoritative filings and provider documentation. Multibagger radar is a screening workflow, not a forecast or investment advice.
### MCP data stack

The MCP Docker image installs the ASET universe, price and SEC extras by default so the automatic multibagger pipeline has a working global screening path out of the box.

To change the installed optional data set, override the Docker build argument:

ASET_DATA_EXTRAS=universe,prices,china,sec,macro

OpenBB provider extensions remain separate optional extras because OpenBB 5.x is a provider-extension architecture.
