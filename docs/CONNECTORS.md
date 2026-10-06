# ASET Connectors for ChatGPT, Claude, and Manus

ASET exposes a read-only [Model Context Protocol](https://modelcontextprotocol.io/) server. MCP is the shared integration layer: the same typed tools can be discovered by ChatGPT, Claude, Manus, and other MCP hosts.

The repository contains two complementary MCP surfaces. The core ASET MCP exposes normalized securities/prices/metrics; the SignalDesk MCP is the productized fundamentals and multi-agent screening surface described below.

## SignalDesk multibagger agents

The SignalDesk MCP adds read-only tools for large-universe equity research:

- research_director: end-to-end orchestrated read-only research run with batching, de-duplication, source reconciliation, evidence gating and a deep-diligence queue.
- cross_check_sources: field-level Yahoo Finance vs configured ASET-provider reconciliation with match/close/conflict/unavailable states and verification grades.
- export_research_dataset: stable `aset_research_workbook.v1` payload containing raw 5-year statement history, verification and provenance for Excel materialization.
- analyze_stock: single-ticker provider-backed fundamentals.
- screen_universe: bounded parallel screening across many tickers.
- compare_stocks: normalized side-by-side comparison.
- multibagger_radar: deterministic multi-year compounding candidate funnel.
- check_signaldesk: service health.
- get_signaldesk_config: non-secret provider/configuration metadata.

Use the host prompts in `agents/multibagger/prompts/` and `agents/research-director/prompts/` to run the workflow in ChatGPT, Claude and Manus. Research Director handles the orchestration and cross-provider checks; the host still independently verifies material business claims with primary sources. A screening score is not a return forecast.

The server is intentionally read-only. It has no trading, brokerage, payment, filesystem, or arbitrary code-execution tool.

## Install

From a clean ASET checkout:

```bash
python -m pip install -e '.[connectors]'
```

Run locally over stdio:

```bash
aset-mcp
```

Run as a remote Streamable HTTP server:

```bash
ASET_ALLOWED_HOSTS=your-mcp-host.example.com \
  aset-mcp --transport streamable-http --host 0.0.0.0 --port 8001
```

Put TLS, authentication, rate limiting, and a reverse proxy in front of a public deployment. Do not expose an unauthenticated production research service containing private provider credentials.

## Claude Desktop and Claude Code

For Claude Desktop, copy the server entry from [`integrations/claude_desktop_config.example.json`](../integrations/claude_desktop_config.example.json) into the Claude Desktop MCP configuration and replace the checkout path.

For Claude Code, from the ASET directory run:

```bash
claude mcp add aset -- python -m stock_analyzer.mcp_server
claude mcp list
```

Or copy [`integrations/mcp.json.example`](../integrations/mcp.json.example) to `.mcp.json` in a project that should use ASET. Review and approve the project-scoped server when Claude asks.

## ChatGPT / OpenAI API

For a public deployment, connect the Streamable HTTP endpoint at `https://YOUR_HOST/mcp`. The OpenAI Responses API shape is:

```bash
curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "YOUR_MCP_COMPATIBLE_MODEL",
    "input": "Show ASET price history and calculate its return.",
    "tools": [{
      "type": "mcp",
      "server_label": "aset",
      "server_description": "Read-only ASET equity research tools",
      "server_url": "https://YOUR_HOST/mcp",
      "allowed_tools": ["aset_get_security", "aset_get_prices", "aset_calculate_metrics"],
      "require_approval": "always"
    }]
  }'
```

OpenAI's MCP guidance recommends trusting and reviewing remote servers carefully because a remote MCP server can receive model context. Keep approval enabled until the deployment and tool behavior are verified.

## Manus

For a local Manus development environment, use the same stdio command after installing the connector extra:

```text
command: python
args: -m stock_analyzer.mcp_server
working directory: /absolute/path/to/ASET
```

For a hosted Manus connector, register the HTTPS Streamable HTTP endpoint:

```text
https://YOUR_HOST/mcp
```

Use the Manus connector configuration flow to provide the endpoint and, if the deployment requires it, OAuth or bearer authentication. Never place provider API keys in this repository or in chat messages.

## Connector security checklist

Use a dedicated read-only data-provider identity, explicit allowed hosts and origins, HTTPS, authentication for non-public data, request logging without secrets, rate limits, and a short provider timeout. Keep `require_approval` enabled for new remote connections. Validate the connected tool list before allowing a model to use it, and remember that research output is not investment advice.
