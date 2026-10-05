# ChatGPT connector

ASET uses the standard Model Context Protocol (MCP) so ChatGPT can call the same research tools as the Windows and web clients.

## Remote setup

1. Deploy the ASET MCP server behind HTTPS.
2. Use the endpoint ending in /mcp.
3. In a ChatGPT workspace with custom MCP apps enabled, create a custom app and enter the MCP endpoint.
4. Scan tools.
5. Test in a new chat with a request such as: Scan my stock universe with ASET and find the strongest multi-year compounding candidates.

Example:

~~~text
https://research.example.com/mcp
~~~

## Multi-stock agent workflow

The recommended agent uses these tools in order:

- check_signaldesk
- get_signaldesk_config
- screen_universe
- compare_stocks
- multibagger_radar
- analyze_stock

For a universe larger than one batch, ChatGPT should partition the tickers into chunks, screen each chunk, merge the top candidates, compare the merged shortlist, and then use its own research/web capabilities for primary-source diligence.

The MCP server returns compact candidate output rather than thousands of raw records, which keeps chat context manageable.

## Read-only safety

No trade execution is exposed.

The deterministic ASET score is a research-priority signal only. ChatGPT must independently verify moat, runway, valuation, catalysts, dilution, governance and the thesis-killer before presenting an A-level candidate.

Do not store Alpha Vantage credentials in ChatGPT configuration. Keep provider keys in the self-hosted server environment.

Official references:

- https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt
- https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk
