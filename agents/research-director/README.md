# ASET Research Director Agent

ASET Research Director is the orchestration agent for the ASET equity-research stack.

It sits above the deterministic SignalDesk/MCP tools and turns a ticker universe into a traceable research queue:

1. preflight the research service and provider configuration;
2. normalize and partition the universe;
3. screen every batch without imputing missing data;
4. merge and de-duplicate the strongest candidates;
5. run a normalized cross-company comparison;
6. apply evidence and risk gates;
7. return a compact deep-diligence queue plus explicit data gaps.

The agent is intentionally research-first and execution-free. It does not place brokerage orders, invent facts, or turn a screen score into a guaranteed-return prediction.

## Why this is different from the existing radar

multibagger_radar is a deterministic scoring funnel.

Research Director is the workflow orchestrator. It manages the full sequence, preserves stage metadata, records failures, applies configurable gates, and produces a handoff package for a host model to perform primary-source diligence.

## Tool surface

The MCP server exposes:

- research_director — full orchestrated research run;
- screen_universe — bounded quantitative screen;
- compare_stocks — normalized comparison;
- multibagger_radar — deterministic candidate funnel;
- analyze_stock — single-company provider-backed research;
- check_signaldesk — service health;
- get_signaldesk_config — safe provider/configuration metadata.

## Output contract

A run returns run_id, objective, preflight, universe, stages, shortlist, deep_diligence_queue, rejections, data_gaps, failures, and research_rules.

Every candidate carries the underlying deterministic score and risk flags. Missing values remain missing.

## Production posture

The agent is designed for large universes up to the configured ASET limit. Batch size, shortlist size, and deep-diligence queue size are bounded to keep tool responses predictable.

Primary-source business diligence remains a host-side responsibility. A host such as ChatGPT should use the returned queue as the starting point for filings, investor relations materials, earnings calls and independent market evidence.
