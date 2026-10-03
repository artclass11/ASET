"""ASET stock research engine."""

from .analytics import MetricResult, annualized_volatility, maximum_drawdown, simple_return
from .config import Settings, cli
from .domain import DataQuality, PriceObservation, Provenance, Security
from .providers import FixtureMarketDataProvider, MarketDataProvider, make_fixture_provider

try:
    from .api import create_app
except ImportError:  # pragma: no cover - allows domain-only installations
    create_app = None  # type: ignore[assignment]

__all__ = [
    "DataQuality",
    "FixtureMarketDataProvider",
    "MarketDataProvider",
    "MetricResult",
    "PriceObservation",
    "Provenance",
    "Security",
    "Settings",
    "annualized_volatility",
    "create_app",
    "cli",
    "maximum_drawdown",
    "make_fixture_provider",
    "simple_return",
]
