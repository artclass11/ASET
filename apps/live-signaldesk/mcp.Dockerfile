FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8100 \
    MCP_PATH=/mcp \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY stock_analyzer ./stock_analyzer
COPY apps/live-signaldesk/requirements-mcp.txt ./requirements-mcp.txt
COPY apps/live-signaldesk/mcp_server.py ./mcp_server.py

RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir -r requirements-mcp.txt

USER 65532:65532
EXPOSE 8100

CMD ["python", "mcp_server.py"]
