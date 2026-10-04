"""Provider interfaces and lazy live integrations for ASET."""

from __future__ import annotations

import importlib.util
import os
from datetime import date, datetime, timezone, timedelta
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
        self._prices: dict[str, tuple[PriceObservation, ...]] = {}
        for key, value in prices.items():
            observations = tuple(value)
            dates = [item.trading_date for item in observations]
            if dates != sorted(set(dates)):
                raise ValueError(f"fixture observations for {key} must be unique and ordered")
            self._prices[key.upper()] = observations

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


class YFinanceMarketDataProvider:
    """Lazy yfinance-backed provider for the ASET core price API."""

    name = "yfinance"

    def __init__(self, *, timeout: float | None = None) -> None:
        if importlib.util.find_spec("yfinance") is None:
            raise RuntimeError("yfinance is not installed; install ASET with the [prices] extra")
        self.timeout = timeout if timeout is not None else float(os.getenv("YFINANCE_TIMEOUT_SECONDS", "8"))

    @staticmethod
    def _ticker(symbol: str):
        import yfinance as yf

        return yf.Ticker(symbol.strip().upper())

    def get_security(self, symbol: str) -> Security:
        normalized = symbol.strip().upper()
        ticker = self._ticker(normalized)
        info = ticker.get_info()
        currency = str(info.get("currency") or "USD").upper()
        if len(currency) != 3 or not currency.isalpha():
            currency = "USD"
        observed = datetime.now(timezone.utc)
        return Security(
            normalized,
            str(info.get("longName") or info.get("shortName") or normalized),
            str(info.get("exchange") or "UNKNOWN"),
            currency,
            Provenance(
                self.name,
                f"https://finance.yahoo.com/quote/{normalized}/",
                observed,
                observed.date(),
            ),
        )

    def get_prices(self, symbol: str, start: date, end: date) -> Sequence[PriceObservation]:
        if start > end:
            raise ValueError("start must not be after end")
        normalized = symbol.strip().upper()
        ticker = self._ticker(normalized)
        end_exclusive = end + timedelta(days=1)
        frame = ticker.history(
            start=start.isoformat(),
            end=end_exclusive.isoformat(),
            auto_adjust=False,
            actions=False,
            timeout=self.timeout,
        )
        if frame is None or frame.empty:
            raise KeyError(f"yfinance returned no prices for {normalized}")

        security = self.get_security(normalized)
        observations: list[PriceObservation] = []
        for timestamp, row in frame.iterrows():
            trading_date = timestamp.date() if hasattr(timestamp, "date") else date.fromisoformat(str(timestamp)[:10])
            close = row.get("Close")
            if close is None:
                continue
            try:
                close_value = Decimal(str(float(close)))
            except (TypeError, ValueError):
                continue
            if close_value <= 0:
                continue
            observations.append(
                PriceObservation(
                    security=security,
                    trading_date=trading_date,
                    close=close_value,
                    provenance=Provenance(
                        self.name,
                        f"https://finance.yahoo.com/quote/{normalized}/history/",
                        datetime.now(timezone.utc),
                        trading_date,
                    ),
                )
            )
        if not observations:
            raise KeyError(f"yfinance returned no usable prices for {normalized}")
        return tuple(observations)


def make_fixture_provider() -> FixtureMarketDataProvider:
    """Return a small reproducible ASET demo dataset."""
    observed_at = datetime(2024, 1, 5, tzinfo=timezone.utc)
    security_provenance = Provenance("fixture", "fixture://securities", observed_at, date(2024, 1, 5))
    security = Security("ASET", "ASET Demo Corp", "NASDAQ", "USD", security_provenance)
    values = (100, 102, 101, 105, 110)
    prices = tuple(
        PriceObservation(
            security=security,
            trading_date=date(2024, 1, index + 1),
            close=Decimal(value),
            provenance=Provenance(
                "fixture", f"fixture://prices/ASET/{index + 1}", observed_at, date(2024, 1, index + 1)
            ),
        )
        for index, value in enumerate(values)
    )
    return FixtureMarketDataProvider({"ASET": security}, {"ASET": prices})


def make_provider_from_env(provider: str | None = None):
    """Select fixture or a real provider without a hidden live-to-fixture fallback."""
    provider = (provider if provider is not None else os.getenv("ASET_PROVIDER", "fixture")).strip().lower()
    if provider in ("", "fixture", "demo", "development"):
        return make_fixture_provider()
    if provider == "yfinance":
        return YFinanceMarketDataProvider()
    raise ValueError(
        "Unsupported ASET_PROVIDER. Use 'fixture' for deterministic development or 'yfinance' for live price data."
    )


__all__ = [
    "FixtureMarketDataProvider",
    "MarketDataProvider",
    "YFinanceMarketDataProvider",
    "make_fixture_provider",
    "make_provider_from_env",
]
