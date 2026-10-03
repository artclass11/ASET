# Security Policy

## Supported scope
Security reports for ASET are welcome for:
- authentication or authorization defects
- secret exposure
- unsafe file handling
- injection vulnerabilities
- dependency or CI configuration issues
- data-isolation failures
- server-side request or execution vulnerabilities

## Reporting
Please do not publish sensitive exploit details in a public issue.
For a report involving private credentials or a high-impact vulnerability, contact the project owner through GitHub's available private reporting mechanism or Instagram:

https://www.instagram.com/amormagics/

## Secrets
Never commit API keys, access tokens, cloud credentials, private datasets, .env files, or customer data.
Use environment variables or a managed secret store for deployment credentials.
The application never provides a fake credential fallback: missing credentials must fail closed or use an explicitly documented offline fixture mode.

## Application controls

- The production research API is read-only and has no brokerage, custody, wallet, or order-submission capability.
- Host allowlists and CORS origins are explicit configuration; wildcard origins are not permitted for deployment.
- Responses include security headers, request correlation IDs, and bounded query sizes.
- Provider failures return stable public errors without exposing upstream exceptions, credentials, or internal paths.
- External data is treated as untrusted input and validated before normalization or calculation.

## Supply-chain controls

CI installs from the root package metadata, runs Ruff, mypy, tests, Bandit, and pip-audit, and uses read-only GitHub token permissions for quality jobs. Dependency changes should be reviewed and pinned where provider compatibility requires a fixed version.

## Data safety
Treat external market/fundamental data as untrusted input. Validate schemas, units, dates and provenance before material calculations.

## Scope boundary
ASET is a research and quantitative analytics platform. It should not be extended with custody, broker order submission, or transaction execution without an explicit architectural and security review.
