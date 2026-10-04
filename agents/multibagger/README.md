# ASET Multibagger Research Swarm

ASET provides a common research protocol for ChatGPT, Claude and Manus.

## Fast path

Use aset_auto_multibagger_screen for a new large-universe request. The staged pipeline performs source-health routing, broad universe discovery, fast numeric filtering, bounded deep enrichment, deterministic ranking and optional primary filing verification.

For extremely large universes, the host can partition work further, but the preferred path is the single pipeline call so workflow state stays compact.

## Candidate discipline

An A-level result is a research priority, not a guaranteed multibagger. Independently verify moat, runway, reinvestment, dilution, accounting quality, catalysts, expectations and valuation.

## Cross-host tools

aset_source_health
aset_route_dataset
aset_filter_universe
aset_yfinance_screen
aset_auto_multibagger_screen
analyze_stock
compare_stocks
multibagger_radar

## Data selection

ASET chooses projects by task, geography, scale, stage, package availability and credentials. FinanceDatabase is used for broad metadata, yfinance for fast global screening and price data, AKShare for China routes, SEC/Edgar tooling for U.S. filings, and concrete OpenBB extensions when installed.

Do not use fixture data for live research.

## Scaling

The pipeline limits expensive per-company enrichment. Provider quotas, data licenses and network limits still determine practical throughput. The default is a 20,000-record metadata universe, up to 1,000 fast-screen results and 25 deep fundamental enrichments.