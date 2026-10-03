# ASET Operations Guide

## Local startup

```bash
python -m pip install -e '.[dev]'
stock-research
```

The local API listens on `127.0.0.1:8000` by default. The service is read-only and does not submit trades or access broker accounts.

## Configuration

- `ASET_ENVIRONMENT`: deployment name; defaults to `development`.
- `ASET_APP_NAME`: service title.
- `ASET_ALLOWED_ORIGINS`: comma-separated browser origins. Empty means no cross-origin browser access.
- `ASET_MAX_PRICE_POINTS`: maximum points returned by one request; defaults to 500 and is capped at 10,000.

## Probes

- `GET /api/v1/health` verifies the process is responding.
- `GET /api/v1/readiness` verifies the configured provider boundary is available.
- Every response includes `x-request-id`; clients may provide a UUID to correlate requests.

## Failure behavior

Provider lookup failures return `404`. Provider runtime failures return `503` with a stable error code and never expose exception text, credentials, or upstream internals. Invalid dates and limits return `422`.

## Production checklist

- Set an explicit allowlist in `ASET_ALLOWED_ORIGINS`.
- Run behind TLS and an authenticated gateway if exposed beyond a trusted network.
- Configure upstream provider timeouts, rate limits, and identity according to that provider's policy.
- Monitor response status by endpoint, provider failure rate, latency, and `x-request-id` correlation.
- Keep research data immutable by preserving provider, source, observation time, as-of period, and quality status.
- Run compile, tests, Ruff, mypy, and pip-audit in CI before deployment.
