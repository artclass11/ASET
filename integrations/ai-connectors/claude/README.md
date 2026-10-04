# Claude connector

ASET's MCP server can be used as a remote custom connector in Claude and Claude Desktop.

## Remote setup

1. Deploy the ASET MCP endpoint over HTTPS.
2. In Claude or Claude Desktop, open Settings > Connectors.
3. Choose Add custom connector.
4. Enter the ASET MCP URL.
5. Connect/authenticate as required.
6. Enable ASET tools in chat.

Example:

~~~text
https://research.example.com/mcp
~~~

Claude supports Streamable HTTP and SSE remote MCP servers; ASET uses Streamable HTTP for new deployments.

## Claude Code / local MCP

For a local machine, configure the MCP server as a stdio process:

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

Do not store Alpha Vantage credentials in Claude configuration.

Official reference:

https://support.anthropic.com/en/articles/11503834-building-custom-integrations-via-remote-mcp-servers
