# ASET Yahoo Finance Plugin

A private ChatGPT plugin that connects to a community-hosted, yfinance-backed MCP server for Yahoo Finance research.

## Remote MCP

`https://janus.bradensbay.com/mcp`

The remote deployment is third-party/community-hosted. It is not an official Yahoo Finance service and can be delayed, rate-limited, or unavailable.

## Open-source local server

The ASET repository also contains the user's own yfinance implementation:

`stock_analyzer/yfinance_mcp.py`

Run it locally with:

`aset-yfinance-mcp`

or expose it with Streamable HTTP using:

`aset-yfinance-mcp --transport streamable-http --host 0.0.0.0 --port 8101`

The server is read-only and includes quote, history, company info, financial statements, analyst data, options, corporate actions, news, search and quote comparison tools.
