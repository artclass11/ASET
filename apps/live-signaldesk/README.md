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

## Data provider

The app uses Alpha Vantage's official query API for `GLOBAL_QUOTE`, `OVERVIEW`, `INCOME_STATEMENT`, and `BALANCE_SHEET`.

Alpha Vantage documents that the default quote endpoint may be end-of-day, while realtime and 15-minute delayed US market-data access depends on the appropriate entitlement. See: https://www.alphavantage.co/documentation/

When `ALPHAVANTAGE_API_KEY` is not configured, only IBM uses the clearly labeled Alpha Vantage demo preview. No synthetic stock values are generated.

## Local Docker test

Copy the environment example to `.env` and set your API key.

```bash
cp .env.example .env
docker compose up -d --build
```

Open `http://localhost:8000`.

## Self-hosted deployment

This directory is intentionally portable. It contains a standard Dockerfile and Docker Compose definition, so it can run on a Linux VPS, dedicated server, home lab or an open-source deployment platform.

### Coolify

Coolify supports Git repositories using Dockerfile or Docker Compose deployments and can run workloads on infrastructure you control.

Repository: `https://github.com/artclass11/ASET`

Application root: `apps/live-signaldesk`

For the Windows desktop client, allow these origins (or your exact controlled origins) with `SIGNALDESK_CORS_ORIGINS`:

`http://tauri.localhost,http://localhost:1420,http://127.0.0.1:1420`

Set secret:

`ALPHAVANTAGE_API_KEY`

Expose port `8000`, attach your domain, enable HTTPS, and deploy.

Coolify: https://coolify.io/
Deployment guide: https://coolify.io/docs/applications/choose-deployment-method

## API

`GET /health`

`GET /api/v1/config`

`GET /api/v1/research/IBM`

`GET /api/v1/research/AAPL?entitlement=delayed`

`GET /api/v1/research/MSFT?entitlement=realtime`

## Security

Never commit `.env` or API keys. The browser talks only to the SignalDesk server; the Alpha Vantage credential stays in the server environment.

The container uses a read-only filesystem with a temporary `/tmp` mount and `no-new-privileges`.

## Commercial Pro

The public app is the live demonstration surface. Commercial licensing can add additional providers, report generation, scheduled refresh, authentication, team workspaces and deployment support.

Purchase/support: https://www.instagram.com/amormagics/

Direct message: https://ig.me/m/amormagics/

## Disclaimer

Market data may be delayed or entitlement-dependent. Validate material figures against authoritative filings and provider documentation. This is research software, not investment advice.