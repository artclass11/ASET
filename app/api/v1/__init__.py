from __future__ import annotations

import json
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="ASET Dashboard", page_icon="📈", layout="wide")


st.markdown(
    """
    <style>
    .stApp {
        background: #0a0f1a;
        color: #e6edf3;
    }
    .stSidebar {
        background: #0f172a;
    }
    .css-1d391kg, .css-1wrcr25, .css-17eq0hr {
        background: #111827;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }
    .stDataFrame {
        background: #0b1220;
        color: #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("ASET | Advanced Stock Analysis Engine Toolkit")
st.caption("Minimal black enterprise dashboard for stock analysis")


API_URL = "http://localhost:8000/api/v1"


with st.sidebar:
    st.header("Controls")
    symbol = st.text_input("Ticker", value="AAPL")
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
    refresh = st.button("Refresh")


if refresh or symbol:
    try:
        response = requests.get(f"{API_URL}/stocks/{symbol.upper()}", timeout=20)
        response.raise_for_status()
        quote = response.json()["data"]
        historical = requests.get(
            f"{API_URL}/stocks/{symbol.upper()}/historical",
            params={"period": period, "interval": "1d"},
            timeout=20,
        )
        historical.raise_for_status()
        history = historical.json()["history"]
        df = pd.DataFrame(history)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date")

        price = quote.get("current_price", 0)
        prev_close = quote.get("previous_close", price)
        change = ((price - prev_close) / prev_close * 100) if prev_close else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${price:,.2f}")
        col2.metric("Change %", f"{change:.2f}%")
        col3.metric("Symbol", symbol.upper())

        if not df.empty and {"Date", "Close"}.issubset(df.columns):
            fig = px.line(
                df,
                x="Date",
                y="Close",
                title=f"{symbol.upper()} Price Trend",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

        technical = requests.get(f"{API_URL}/stocks/{symbol.upper()}/analysis/technical", timeout=20)
        technical.raise_for_status()
        tech_json = technical.json()["technical"]

        st.subheader("Technical Analysis")
        st.json(tech_json)

    except requests.RequestException as exc:
        st.error(f"Failed to load data: {exc}")

else:
    st.info("Enter a ticker symbol to begin analysis.")
