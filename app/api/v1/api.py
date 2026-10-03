from __future__ import annotations

import numpy as np
import pandas as pd


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def calculate_sma(values: list[float], window: int = 14) -> float | None:
    if len(values) < window:
        return None
    return float(np.mean(values[-window:]))


def calculate_ema(values: list[float], span: int = 14) -> float | None:
    if not values:
        return None
    series = pd.Series(values)
    return float(series.ewm(span=span, adjust=False).mean().iloc[-1])


def calculate_rsi(values: list[float], window: int = 14) -> float | None:
    if len(values) < window + 1:
        return None
    series = pd.Series(values)
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.rolling(window=window).mean().iloc[-1]
    avg_loss = down.rolling(window=window).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def calculate_macd(values: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, float | None]:
    if len(values) < slow:
        return {"macd": None, "signal": None, "histogram": None}

    series = pd.Series(values)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def calculate_bollinger(values: list[float], window: int = 20, k: float = 2.0) -> dict[str, float | None]:
    if len(values) < window:
        return {"sma": None, "upper": None, "lower": None}

    series = pd.Series(values)
    sma = series.rolling(window=window).mean().iloc[-1]
    std = series.rolling(window=window).std().iloc[-1]
    upper = sma + (k * std)
    lower = sma - (k * std)

    return {"sma": float(sma), "upper": float(upper), "lower": float(lower)}


def analyze_series(values: list[float]) -> dict[str, float | None | dict[str, float | None]]:
    clean = [safe_float(v) for v in values]
    clean = [v for v in clean if not np.isnan(v)]

    if not clean:
        return {
            "sma_14": None,
            "ema_14": None,
            "rsi_14": None,
            "macd": None,
            "bollinger": None,
            "latest_price": None,
        }

    latest_price = float(clean[-1])
    return {
        "sma_14": calculate_sma(clean, 14),
        "ema_14": calculate_ema(clean, 14),
        "rsi_14": calculate_rsi(clean, 14),
        "macd": calculate_macd(clean),
        "bollinger": calculate_bollinger(clean),
        "latest_price": latest_price,
    }
