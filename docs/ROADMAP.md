# ASET Enterprise Roadmap

## Product mission

ASET is an open-source, provider-neutral platform for institutional-quality public-equity research, screening, analytics, filings, and quantitative backtesting. It is a research system, not a trading execution system.

## Week 1 outcome

Deliver a production-ready vertical slice that can:

1. Normalize market and filing data behind provider interfaces.
2. Preserve provenance, timestamps, currency, units, and data-quality flags.
3. Expose versioned read-only research APIs.
4. Run asynchronously for expensive research jobs.
5. Persist results behind PostgreSQL-compatible repositories and cache hot reads.
6. Pass automated tests, linting, type checks, and dependency/security checks.

## Target architecture

```text
Providers (Yahoo / SEC / AKShare / FinanceDatabase)
                |
        Normalization + provenance
                |
     Domain models + quality policies
                |
  Research services (screening, filings, analytics)
                |
 API / job workers / CLI / notebooks
                |
 PostgreSQL + object storage + Redis cache
```

## Non-negotiable engineering standards

- No provider-specific response shapes leak into the domain layer.
- Every material observation includes `source`, `observed_at`, `as_of`, and a quality status.
- API contracts are versioned and documented with OpenAPI.
- No credentials, fake API keys, or permissive production CORS defaults are committed.
- Research endpoints are read-only; trade execution is out of scope.
- All new behavior requires tests and structured logs.
- Provider failures degrade explicitly and never silently become fabricated data.

## Parallel workstreams

### A — Core domain and provider contracts

Build typed models for securities, prices, fundamentals, filings, provenance, and quality flags. Add provider protocols and a deterministic in-memory fixture provider.

### B — Data ingestion and provider adapters

Implement the first production adapter (SEC filings or Yahoo Finance), retries, rate-limit handling, timeouts, response normalization, and fixture-backed contract tests.

### C — Research API

Replace the prototype API with a versioned `/api/v1` read-only service. Add health/readiness, request IDs, pagination, error envelopes, and dependency injection.

### D — Persistence and jobs

Define repository interfaces and PostgreSQL/Redis-compatible implementations. Add job lifecycle models and an async worker boundary; local mode may use an in-process adapter.

### E — Quant analytics

Add a deterministic analytics module for returns, volatility, drawdown, and screening. Include explicit lookback periods, calendar handling, and tests for edge cases.

### F — Platform engineering

Add CI gates, formatting, linting, typing, dependency auditing, container build, local compose, observability conventions, and security documentation.

## Delivery sequence

- **Day 1:** contracts, repository cleanup, CI, issue ownership.
- **Day 2:** domain models and fixture provider.
- **Day 3:** first live provider adapter and persistence interfaces.
- **Day 4:** research API and job boundary.
- **Day 5:** analytics vertical slice and integration tests.
- **Day 6:** containerization, observability, security, and documentation.
- **Day 7:** end-to-end demo, performance pass, failure-mode review, release checklist.

## Definition of done

- `pytest`, `ruff`, and `mypy` pass in CI.
- A fresh checkout can run the API locally with documented commands.
- The demo can ingest fixture data, run one research query, and return provenance-rich results.
- Provider outages and malformed data produce explicit, observable errors.
- No production secret or external transaction capability is present.
