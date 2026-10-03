"""Provider interfaces and deterministic fixtures for ASET."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Protocol, Sequence

from .domain import PriceObservation, Provenance, Security


class MarketDataProvider(Protocol):
    name: str

    def get_security(self, symbol: str) -> Security: ...

    def get_prices(self, symbol: str, start: date, end: date) -> Sequence[PriceObservation]: ...


class FixtureMarketDataProvider:
    """Deterministic provider used for tests, demos, and local development."""

    name = "fixture"

    def __init__(self, securities: dict[str, Security], prices: dict[str, Sequence[PriceObservation]]) -> None:
        self._securities = {key.upper(): value for key, value in securities.items()}
        self._prices = {key.upper(): tuple(value) for key, value in prices.items()}

    def get_security(self, symbol: str) -> Security:
        try:
            return self._securities[symbol.upper()]
        except KeyError as exc:
            raise KeyError(f"fixture security not found: {symbol}") from exc

    def get_prices(self, symbol: str, start: date, end: date) -> Sequence[PriceObservation]:
        if start > end:
            raise ValueError("start must not be after end")
        symbol = symbol.upper()
        if symbol not in self._prices:
            raise KeyError(f"fixture prices not found: {symbol}")
        return tuple(item for item in self._prices[symbol] if start <= item.trading_date <= end)


def make_fixture_provider() -> FixtureMarketDataProvider:
    """Return a small reproducible ASET demo dataset."""
    security_provenance = Provenance("fixture", "fixture://securities", datetime.now(timezone.utc), date(2024, 1, 5))
    security = Security("ASET", "ASET Demo Corp", "NASDAQ", "USD", security_provenance)
    values = (100, 102, 101, 105, 110)
    prices = tuple(
        PriceObservation(
            security=security,
            trading_date=date(2024, 1, index + 1),
            close=Decimal(value),
            provenance=Provenance("fixture", f"fixture://prices/ASET/{index + 1}", datetime.now(timezone.utc), date(2024, 1, index + 1)),
        )
        for index, value in enumerate(values)
    )
    return FixtureMarketDataProvider({"ASET": security}, {"ASET": prices})
