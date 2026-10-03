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

## Data safety
Treat external market/fundamental data as untrusted input. Validate schemas, units, dates and provenance before material calculations.

## Scope boundary
ASET is a research and quantitative analytics platform. It should not be extended with custody, broker order submission, or transaction execution without an explicit architectural and security review.