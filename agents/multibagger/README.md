# ASET Multibagger Research Swarm

ASET now has a host-neutral research protocol for ChatGPT, Claude and Manus.

The goal is not to predict a guaranteed multibagger. The system creates a repeatable funnel:

1. Screen thousands of tickers using provider-backed fundamentals.
2. Rank candidates with deterministic growth, quality, balance-sheet, valuation and evidence signals.
3. Compare the strongest names side-by-side.
4. Force independent diligence on the business, moat, runway, capital allocation, dilution, cyclicality, governance, catalysts and valuation.
5. Run a bull case and an adversarial skeptic case.
6. Return a research-priority shortlist with explicit evidence gaps and rejection conditions.

## Architecture

    +----------------------+
    | ChatGPT / Claude /   |
    | Manus host agent     |
    +----------+-----------+
               |
               | MCP
               v
    +----------------------+
    | ASET SignalDesk MCP |
    +----------+-----------+
               |
      +--------+--------+
      |                 |
      v                 v
 SignalDesk API     Deterministic
 / provider data   agent_engine.py
      |                 |
      +--------+--------+
               |
               v
        Candidate funnel
               |
               v
 Host-side primary-source diligence

## Large-universe workflow

For a universe larger than the MCP batch setting, the host should partition the symbols into independent chunks, call screen_universe for each chunk, keep only the top candidates from every chunk, merge and de-duplicate them, then call compare_stocks on the merged shortlist.

This keeps responses compact while allowing the overall process to cover thousands of symbols.

The current SignalDesk app is Alpha Vantage-backed. Provider quotas and entitlements still apply. For serious thousands-of-symbol production scans, use a provider/data tier that licenses the required breadth and throughput, while retaining ASET's normalized research contract.

## Scoring

agent_engine.py calculates a deterministic screening score from:

- multi-year revenue growth;
- multi-year net-income growth;
- latest profit growth;
- net margin and profit consistency;
- debt/cash resilience;
- generic valuation signals;
- evidence completeness.

The score is intentionally not presented as intrinsic value and does not measure moat, management quality, TAM, governance or catalyst probability. Those require separate diligence.

## Candidate discipline

A top-ranked company is only an immediate research candidate.

Before a final research conclusion, the host agent must verify:

- the economic driver actually reaches revenue/orders/backlog/earnings;
- the growth runway is large enough for a multi-year compounding thesis;
- reinvestment opportunities and capital returns are credible;
- valuation leaves room for execution;
- dilution, debt, customer concentration and accounting quality are acceptable;
- a dated catalyst or estimate-revision path exists;
- there is a clear thesis killer.

## Host prompts

- Canonical research director: prompts/system.md
- ChatGPT: prompts/chatgpt.md
- Claude: prompts/claude.md
- Manus: prompts/manus.md

The three host prompts intentionally use the same tool contract so findings can be handed from one model to another without changing the research method.

## Research output schema

Every final candidate should contain:

- symbol and company;
- screen score and tier;
- five-year growth signals;
- valuation signal and key assumptions;
- business thesis;
- exposure proof;
- moat/runway assessment;
- catalyst path;
- key downside risks;
- first rejection test;
- what would make the thesis investable;
- what would kill the thesis;
- evidence links/source identifiers;
- confidence and unresolved gaps.

Never convert a missing value into a guessed value.

## Installation

Deploy the normal ASET SignalDesk API and MCP server, then expose the MCP endpoint over HTTPS for remote hosts. Local users can run the same MCP server with stdio.

See:

- apps/live-signaldesk/README.md
- integrations/ai-connectors/chatgpt/README.md
- integrations/ai-connectors/claude/README.md
- integrations/ai-connectors/manus/README.md
