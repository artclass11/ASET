"""ASET stock research engine."""

from .analytics import MetricResult, annualized_volatility, maximum_drawdown, simple_return
from .config import Settings, cli
from .data_router import DatasetKind, DatasetRequest, route, route_task, route_workflow
from .domain import DataQuality, PriceObservation, Provenance, Security
from .providers import (
    FixtureMarketDataProvider,
    MarketDataProvider,
    YFinanceMarketDataProvider,
    make_fixture_provider,
    make_provider_from_env,
)

try:
    from .api import create_app
except ImportError:  # pragma: no cover - allows domain-only installations
    create_app = None  # type: ignore[assignment]

__all__ = [
    "DataQuality",
    "DatasetKind",
    "DatasetRequest",
    "FixtureMarketDataProvider",
    "MarketDataProvider",
    "YFinanceMarketDataProvider",
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
    "make_provider_from_env",
    "route",
    "route_task",
    "route_workflow",
    "simple_return",
]
