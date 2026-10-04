# Manus connector

ASET provides an MCP server that can be registered with Manus as an MCP connector.

## Setup

1. Deploy the ASET MCP server behind HTTPS.
2. Add/configure the ASET MCP server in Manus integrations.
3. Authorize the connector for your account/workspace.
4. Use the connector ID on Manus tasks, or make it a default connector.

Example task message:

~~~json
{
  "message": {
    "content": "Analyze AAPL with ASET SignalDesk and summarize the five-year income trend.",
    "connectors": ["YOUR_ASET_CONNECTOR_ID"]
  }
}
~~~

The connector UUID is account-specific and is never hard-coded into the public repository.

## Local development

For a local MCP process, use stdio and an MCP-compatible Manus development workflow. For remote use, expose the Streamable HTTP endpoint.

Official references:

- https://open.manus.im/docs/v2/connectors
- https://open.manus.im/docs/v2/connector.list
- https://open.manus.im/docs/v2/open-app
