# ASET Third-Party Notices

This file is a release artifact. Update it for every commercial build from the exact lockfile or environment used to produce that build. Do not treat the current dependency declarations as a completed legal inventory.

## Project code

ASET core code is distributed under the MIT License. Preserve the root `LICENSE` file and its copyright notice in every redistribution of the MIT core or substantial portions of it.

## Runtime dependencies requiring release-time verification

The current Python project declares the following direct runtime dependencies. Record the exact version, license identifier, copyright/notice requirement, and source URL for each one in the release-specific copy of this file:

- pandas
- NumPy
- PyArrow
- OpenPyXL
- yfinance
- FinanceDatabase
- AKShare
- pandas-datareader
- EdgarTools
- sec-edgar-downloader
- FastAPI
- Uvicorn
- python-multipart
- Jinja2

Also inventory all transitive dependencies and any JavaScript, font, image, icon, or documentation assets included in a distributable package.

## Data and provider notices

Software-library licenses do not grant rights to redistribute provider data. For every live-data adapter, record the provider's commercial-use terms, attribution requirements, caching/retention rules, rate limits, and whether customer redistribution is allowed. Keep provider data contracts separate from the software license.

## Release procedure

1. Build from a clean checkout and record the Git commit and package version.
2. Generate an SBOM containing direct and transitive dependencies.
3. Verify each dependency license from authoritative package metadata or the upstream repository.
4. Copy required notices and license texts into the release bundle.
5. Review bundled assets and remove anything without clear commercial rights.
6. Review provider terms for every enabled live-data adapter.
7. Have legal or compliance review the final customer-facing bundle for the target jurisdiction.

## No warranty

This file is a release-management template. It is not a legal opinion and is not a substitute for a lawyer's license and data-rights review.
