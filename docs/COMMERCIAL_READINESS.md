# ASET Commercial Readiness Checklist

This document is an engineering and business checklist, not legal advice. A qualified lawyer in the seller's and customer's jurisdictions should review the final transaction documents before a sale.

## Current conclusion

The repository is under the MIT License. MIT permits commercial use, modification, distribution, sublicensing, and sale, provided the copyright notice and license text are preserved in copies or substantial portions of the software. Selling an MIT-licensed copy does not automatically transfer exclusive ownership of the code.

The current repository is therefore **commercially sellable as open-source software**, subject to the checks below. It is not yet safe to claim that the seller owns every contribution or that every data provider permits commercial redistribution.

## Required before accepting money

### 1. Confirm ownership and contributor rights

- Identify the legal seller: individual, company, or other entity.
- Confirm that the copyright holder named in `LICENSE` is the actual owner or has authority to license the code.
- Obtain written assignments or contributor license agreements from anyone who contributed code, documentation, design, data, or branding outside the seller's employment scope.
- Review all AI-generated or externally copied code and retain evidence of its origin and permitted use.
- Do not rely on Git commit authorship as proof of copyright assignment.

The repository history currently contains more than one author identity, so ownership should be documented before promising an exclusive sale or acquisition.

### 2. Preserve open-source notices

For an MIT-licensed distribution, ship:

- `LICENSE`
- copyright notices
- this project's third-party notices
- license texts required by included dependencies or bundled assets

A commercial Pro package may contain proprietary additions, but it must not remove notices for the MIT core or third-party components.

### 3. Audit dependencies and bundled assets

Create a release-specific software bill of materials (SBOM) and verify the license of every pinned runtime and build dependency. The declared stack includes pandas, NumPy, PyArrow, OpenPyXL, yfinance, FinanceDatabase, AKShare, pandas-datareader, EdgarTools, sec-edgar-downloader, FastAPI, Uvicorn, python-multipart, Jinja2, and their transitive dependencies.

Verify each dependency's current license and notice requirements at release time. Do not assume that a permissive license for the Python wrapper grants rights to redistribute the underlying market data.

### 4. Separate software rights from data rights

The code license does not grant rights to commercialize third-party data. Before selling live-data features, review each provider's terms for:

- commercial use and resale
- redistribution and caching
- derived works and displayed fields
- rate limits and attribution
- user versus organization licensing
- retention and deletion requirements

Treat Yahoo Finance, AKShare, FinanceDatabase, and other upstream sources as separate legal and operational reviews. SEC public filings may be public records, but the delivery method, enrichment, and third-party tooling still require review.

### 5. Use a written customer agreement

Do not use a GitHub README or Instagram message as the complete commercial contract. Use a signed order form or agreement covering:

- licensed modules and version
- license type: open-source, proprietary, subscription, SaaS, or services
- named users, seats, entities, and deployment locations
- permitted copying, modification, and redistribution
- ownership of pre-existing code, custom work, and customer data
- data-provider responsibility and permitted use
- support, updates, maintenance, uptime, and SLA
- fees, taxes, renewal, termination, refunds, and late payment
- confidentiality and security obligations
- warranty disclaimer and limitation of liability
- indemnity allocation and third-party claims
- governing law, venue, and dispute process

### 6. Avoid regulated-finance claims

Market ASET as research software and analytics infrastructure, not as guaranteed investment advice or a trading service. Keep the existing boundary that ASET does not place orders, hold assets, or provide custody. Obtain jurisdiction-specific advice before offering personalized recommendations, managed portfolios, signals marketed as advice, or services to regulated financial institutions.

### 7. Protect customer and user data

Before onboarding real customers, publish or contractually provide:

- privacy policy
- data-processing terms or DPA where required
- retention and deletion policy
- incident-response process
- access-control and audit-log policy
- subprocessor and hosting disclosures

Do not put customer files, credentials, or private datasets into the public repository or demo deployment.

### 8. Protect names and marketing claims

Search trademark registries for `ASET`, `SignalDesk`, logos, and product slogans in the target markets. Check domain and social-media rights. Do not promise exclusivity, patent protection, proprietary data, “risk-free” performance, or ownership of third-party content without evidence.

## Recommended release package

Each commercial release should include a version number, checksum, source or source-offer information for the MIT core, `LICENSE`, `THIRD_PARTY_NOTICES.md`, an SBOM, installation instructions, a security contact, and the signed commercial agreement or order form.

## Final legal gate

A lawyer should review the ownership chain, customer agreement, data-provider terms, privacy obligations, and any financial-regulatory implications. Until that review is complete, sell only clearly scoped software/services under a non-exclusive agreement and do not promise exclusive IP ownership or unrestricted live-data redistribution.
