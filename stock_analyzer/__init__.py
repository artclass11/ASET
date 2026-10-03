"""ASET stock research engine."""

from .analytics import MetricResult, annualized_volatility, maximum_drawdown, simple_return
from .domain import DataQuality, PriceObservation, Provenance, Security
from .providers import FixtureMarketDataProvider, MarketDataProvider, make_fixture_provider

__all__ = [
    "DataQuality",
    "FixtureMarketDataProvider",
    "MarketDataProvider",
    "MetricResult",
    "PriceObservation",
    "Provenance",
    "Security",
    "annualized_volatility",
    "maximum_drawdown",
    "make_fixture_provider",
    "simple_return",
]
