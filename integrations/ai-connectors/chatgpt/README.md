# ChatGPT connector

ASET uses the standard Model Context Protocol (MCP) so ChatGPT can call the same research tools as the Windows and web clients.

## Remote setup

1. Deploy the ASET MCP server behind HTTPS.
2. Use the endpoint ending in /mcp.
3. In a ChatGPT workspace with custom MCP apps enabled, create a custom app and enter the MCP endpoint.
4. Scan tools.
5. Test in a new chat with a request such as: Analyze AAPL with ASET SignalDesk.

Example:

~~~text
https://research.example.com/mcp
~~~

ChatGPT's current custom-MCP flow is documented by OpenAI. ChatGPT connects to remote MCP servers; local servers require a supported tunnel.

## Read-only tools

- analyze_stock
- check_signaldesk
- get_signaldesk_config
- research_prompt

No trade execution is exposed.

Official references:

- https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt
- https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk
