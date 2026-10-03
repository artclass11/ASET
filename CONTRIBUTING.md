# Contributing to ASET

## Scope

ASET is a read-only public-equity research and quantitative analytics platform. Do not add broker integrations, order submission, custody, or transaction execution.

## Agent workflow

1. Start from an up-to-date `main`.
2. Create one focused branch: `agent/<area>-<short-name>`.
3. Keep changes small and independently reviewable.
4. Add tests for every new behavior and failure mode.
5. Never commit secrets, local datasets, or generated credentials.
6. Open a pull request with the problem, design, test evidence, and operational impact.

## Required checks

```bash
python -m compileall .
pytest
ruff check .
mypy .
```

## Data integrity rules

Every normalized observation must preserve provider provenance, observation time, as-of period, units/currency, and a data-quality status. Primary filings should be preferred for material financial figures.

## API rules

- Add new endpoints under `/api/v1`.
- Return stable, documented schemas.
- Include request correlation IDs in logs.
- Use bounded timeouts and explicit error envelopes.
- Keep CORS allowlists configuration-driven; never use `*` with credentials in production.

## Review checklist

- [ ] Scope is limited to one workstream.
- [ ] Tests cover success, empty, malformed, stale, and provider-failure cases.
- [ ] Provenance and quality flags are preserved.
- [ ] No secrets or live credentials are present.
- [ ] API compatibility and migration impact are documented.
- [ ] CI passes locally and in GitHub Actions.
