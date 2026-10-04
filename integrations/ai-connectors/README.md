# ASET AI Connectors

ASET exposes one standards-based Model Context Protocol (MCP) server so the same research tools can be used from compatible AI hosts.

Architecture:

~~~text
ChatGPT / Claude / Manus
        |
        v
     MCP /mcp
        |
        v
 ASET SignalDesk API
        |
        v
 Alpha Vantage
~~~

## What the connector exposes

- analyze_stock — provider-backed quote + fundamentals + five-year income history
- screen_universe — bounded parallel multi-stock screening
- compare_stocks — normalized cross-company comparison
- multibagger_radar — multi-year compounding candidate funnel
- check_signaldesk — API health
- get_signaldesk_config — safe provider/config metadata
- research_prompt — reusable research prompt

All tools are read-only. The connector does not place orders.

For large-universe work, use `agents/multibagger/` as the host-neutral agent protocol. It defines batching, candidate ranking, independent diligence, adversarial review and output requirements for ChatGPT, Claude and Manus.

## Local MCP

From apps/live-signaldesk:

~~~bash
python -m pip install -r requirements-mcp.txt
export SIGNALDESK_API_BASE=http://127.0.0.1:8000
export MCP_TRANSPORT=stdio
python mcp_server.py
~~~

For hosts that accept MCP stdio configuration:

~~~json
{
  "mcpServers": {
    "aset-signaldesk": {
      "command": "python",
      "args": ["/absolute/path/to/ASET/apps/live-signaldesk/mcp_server.py"],
      "env": {
        "SIGNALDESK_API_BASE": "http://127.0.0.1:8000",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
~~~

## Remote MCP

Run the same server with Streamable HTTP:

~~~bash
export SIGNALDESK_API_BASE=https://your-signaldesk.example.com
export MCP_TRANSPORT=streamable-http
export MCP_HOST=0.0.0.0
export MCP_PORT=8100
python mcp_server.py
~~~

The endpoint is:

~~~text
https://your-mcp.example.com/mcp
~~~

Put the endpoint behind HTTPS and an authenticated gateway before exposing it publicly. OAuth 2.1 bearer authorization is the production MCP pattern; the open-source connector is read-only and leaves identity/authentication to the deployment layer.

## ChatGPT

ChatGPT supports custom MCP apps through Developer Mode. Configure the remote MCP endpoint in the ChatGPT app creation flow, scan the tools, then test the draft app in a new chat. ChatGPT connects to remote MCP servers; local servers need a supported tunnel.

Use an endpoint such as:

~~~text
https://YOUR-DOMAIN/mcp
~~~

Then select or mention the created ASET app in chat.

## Claude

Use the same MCP server with an MCP-compatible Claude client.

Remote endpoint:

~~~text
https://YOUR-DOMAIN/mcp
~~~

Local stdio entry:

~~~text
python /absolute/path/to/ASET/apps/live-signaldesk/mcp_server.py
~~~

Claude does not need a separate ASET API integration because the interoperability layer is MCP.

## Manus

Manus supports MCP connector types. Add the remote ASET MCP endpoint in Manus integrations, authorize it as required by the account, and enable the resulting connector for tasks. The Manus API accepts connector IDs on task messages.

Example message shape:

~~~json
{
  "message": {
    "content": "Analyze AAPL with ASET SignalDesk and summarize the five-year income trend.",
    "connectors": ["YOUR_ASET_CONNECTOR_ID"]
  }
}
~~~

The connector ID is created by Manus for the authorized account and is intentionally not hard-coded into the public repository.

## Official references

- OpenAI Apps SDK / MCP: https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk
- OpenAI custom MCP apps: https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Manus connectors: https://open.manus.im/docs/v2/connectors
- Manus Open App: https://open.manus.im/docs/v2/open-app
