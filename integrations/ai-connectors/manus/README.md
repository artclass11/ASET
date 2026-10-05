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
    "content": "Run ASET multibagger radar across my stock universe. Screen in batches, compare the leaders, independently verify the top 10, and return the candidate funnel with evidence gaps.",
    "connectors": ["YOUR_ASET_CONNECTOR_ID"]
  }
}
~~~

## Large-universe operation

Manus should treat the task as a durable batch workflow:

- partition the universe;
- run independent screening batches in parallel where supported;
- checkpoint successful batches;
- retry routine provider failures;
- merge and de-duplicate candidates;
- compare the merged shortlist;
- research the strongest names independently;
- return an audit trail of batches, failures and data gaps.

Never replace a provider failure with a guessed number.

## Local development

For a local MCP process, use stdio and an MCP-compatible Manus development workflow. For remote use, expose the Streamable HTTP endpoint.

The connector UUID is account-specific and is never hard-coded into the public repository.

Official references:

- https://open.manus.im/docs/v2/connectors
- https://open.manus.im/docs/v2/connector.list
- https://open.manus.im/docs/v2/open-app
