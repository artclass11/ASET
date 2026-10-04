# ASET SignalDesk MCP Bundle

This folder contains a Claude Desktop MCP Bundle (MCPB) source package.

MCPB is the current bundle format for local MCP servers in Claude Desktop. The bundle contains a manifest and a local MCP server, and Claude Desktop can install it as a desktop extension.

## Build

Install the MCPB CLI:

~~~bash
npm install -g @anthropic-ai/mcpb
~~~

Then:

~~~bash
cd integrations/claude-mcpb
mcpb pack
~~~

The resulting MCPB file can be installed from Claude Desktop.

The bundle uses the UV runtime, so Python dependencies are declared in pyproject.toml. The local connector is read-only.

Before using it, make sure the ASET SignalDesk API is running on http://127.0.0.1:8000, or adapt the bundle environment to point at your private or remote SignalDesk API.

Do not store an Alpha Vantage API key in the bundle.
