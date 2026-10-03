"""Deterministic quantitative analytics for ASET price observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import sqrt
from statistics import pstdev
from typing import Sequence

from .domain import PriceObservation


@dataclass(frozen=True)
class MetricResult:
    metric: str
    value: float
    start: date
    end: date
    observation_count: int
    provenance_refs: tuple[str, ...]


def _validate(observations: Sequence[PriceObservation]) -> None:
    if len(observations) < 2:
        raise ValueError("at least two observations are required")
    dates = [item.trading_date for item in observations]
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("observations must have unique dates in ascending order")
    if any(item.close <= 0 for item in observations):
        raise ValueError("prices must be positive")


def simple_return(observations: Sequence[PriceObservation]) -> MetricResult:
    _validate(observations)
    value = float(observations[-1].close / observations[0].close - 1)
    return MetricResult(
        "simple_return",
        value,
        observations[0].trading_date,
        observations[-1].trading_date,
        len(observations),
        tuple(item.provenance.source for item in observations),
    )


def annualized_volatility(observations: Sequence[PriceObservation], trading_days: int = 252) -> MetricResult:
    _validate(observations)
    if trading_days <= 0:
        raise ValueError("trading_days must be positive")
    prices = [float(item.close) for item in observations]
    returns = [(current / previous) - 1 for previous, current in zip(prices, prices[1:], strict=False)]
    value = pstdev(returns) * sqrt(trading_days) if len(returns) > 1 else 0.0
    return MetricResult(
        "annualized_volatility",
        value,
        observations[0].trading_date,
        observations[-1].trading_date,
        len(observations),
        tuple(item.provenance.source for item in observations),
    )


def maximum_drawdown(observations: Sequence[PriceObservation]) -> MetricResult:
    _validate(observations)
    peak = float(observations[0].close)
    drawdown = 0.0
    for observation in observations:
        price = float(observation.close)
        peak = max(peak, price)
        drawdown = min(drawdown, (price / peak) - 1)
    return MetricResult(
        "maximum_drawdown",
        drawdown,
        observations[0].trading_date,
        observations[-1].trading_date,
        len(observations),
        tuple(item.provenance.source for item in observations),
    )
