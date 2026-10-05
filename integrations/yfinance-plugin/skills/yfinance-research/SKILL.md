---
name: yfinance-research
description: Use the Yahoo Finance MCP tools for fresh public-market data and company research.
---

# Yahoo Finance research

Use the yfinance-backed MCP server for market-data requests.

Prefer quote tools for the latest available snapshot, history tools for OHLCV, financial-statement tools for annual or quarterly fundamentals, and analyst/options/actions/news tools for specialized research.

Always preserve the provider attribution and fetched timestamp. Yahoo Finance data can be delayed, incomplete, rate-limited, or entitlement-dependent.

Do not invent missing values. For material financial claims, distinguish Yahoo Finance data from authoritative company filings or exchange sources.

This plugin is read-only and does not place trades or manage brokerage accounts.
