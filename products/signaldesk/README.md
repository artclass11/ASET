# ASET SignalDesk — Financial Research Brief Generator

Turn a clean CSV of company fundamentals into a compact analyst-style research brief in seconds.

**Free core:** local, offline, transparent calculations.  
**Pro license:** commercial source package, premium report templates, multi-provider adapters, deployment support and custom integrations.

## Why people can buy it

SignalDesk is designed for investors, analysts, founders, finance educators and research teams who already have data but want a repeatable research workflow.

### Core workflow

`CSV → validate → calculate → compare → generate brief`

The engine can calculate:

- revenue and net-income growth
- average net income when historical columns are supplied
- net margin
- debt-to-cash ratio
- market-cap / net-income multiple proxy
- basic operating and balance-sheet flags
- normalized Markdown and JSON output

No brokerage connection or trading execution is included in the free core.

## Run

Requires Python 3.11+.

```bash
python products/signaldesk/signaldesk.py sample_data/companies.csv --format markdown
```

JSON:

```bash
python products/signaldesk/signaldesk.py sample_data/companies.csv --format json
```

## CSV format

Required:

```text
ticker,company,revenue,net_income,market_cap,debt,cash
```

Optional historical fields:

```text
net_income_y1,net_income_y2,net_income_y3,net_income_y4,net_income_y5
```

The sample dataset is synthetic and exists only for demonstration.

## Commercial edition

The Pro edition is intended for licensed commercial use and can add:

- provider adapters for live market/fundamental data
- scheduled refresh jobs
- PDF/HTML report generation
- saved watchlists
- team workspaces
- API endpoints
- Docker/Kubernetes deployment
- custom branding
- enterprise implementation

Pro functionality is not represented as a fake unlock inside the open-source code. Licensed buyers receive the commercial package separately.

## Purchase / licensing

**Request a SignalDesk Pro license through Instagram:**

https://www.instagram.com/amormagics/

Direct Instagram message:

https://ig.me/m/amormagics

Suggested message:

> I want to buy ASET SignalDesk Pro. Please send pricing, license options and payment details.

Typical commercial packages can be offered as:

| Package | Example positioning |
|---|---|
| Personal | Single user / internal research |
| Studio | Small research team |
| Enterprise | Deployment + customization |

Final pricing and scope should be agreed directly with the seller.

## Important

SignalDesk is a research utility, not investment advice. Financial metrics depend on the quality, period and definitions of the supplied data. Validate important figures against primary filings and authoritative market-data sources.

## License

The open-source core in this repository remains under the repository's project license. Commercial Pro materials, implementation services and custom integrations are sold separately under their own terms.
