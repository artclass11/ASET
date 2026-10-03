from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf


class FundamentalAnalyzer:
    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self.ticker = yf.Ticker(self.symbol)

    def get_snapshot(self) -> dict[str, Any]:
        info = self.ticker.info
        if not info:
            raise ValueError(f"No fundamental data found for {self.symbol}")

        return {
            "symbol": self.symbol,
            "company_name": info.get("longName") or info.get("shortName") or self.symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "price_to_book": info.get("priceToBook"),
            "enterprise_value": info.get("enterpriseValue"),
            "gross_profit": info.get("grossProfits"),
            "revenue": info.get("totalRevenue"),
            "earnings_growth": info.get("earningsGrowth"),
            "revenue_growth": info.get("revenueGrowth"),
            "target_mean_price": info.get("targetMeanPrice"),
        }

    def get_financials(self) -> dict[str, Any]:
        financials = self.ticker.financials
        balance_sheet = self.ticker.balance_sheet
        cashflow = self.ticker.cashflow

        return {
            "financials": financials.head().to_dict() if not financials.empty else {},
            "balance_sheet": balance_sheet.head().to_dict() if not balance_sheet.empty else {},
            "cashflow": cashflow.head().to_dict() if not cashflow.empty else {},
        }
