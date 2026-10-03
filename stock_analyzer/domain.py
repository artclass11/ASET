"""Provider-neutral domain models for ASET research data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Iterable


class DataQuality(StrEnum):
    VERIFIED = "verified"
    ESTIMATED = "estimated"
    STALE = "stale"
    PARTIAL = "partial"
    INVALID = "invalid"


@dataclass(frozen=True)
class Provenance:
    provider: str
    source: str
    observed_at: datetime
    as_of: date
    quality: DataQuality = DataQuality.VERIFIED

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.provider.strip() or not self.source.strip():
            raise ValueError("provider and source are required")


@dataclass(frozen=True)
class Security:
    symbol: str
    name: str
    exchange: str
    currency: str
    provenance: Provenance

    def __post_init__(self) -> None:
        for value, label in (
            (self.symbol, "symbol"),
            (self.name, "name"),
            (self.exchange, "exchange"),
            (self.currency, "currency"),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")
        if self.currency.upper() != self.currency:
            raise ValueError("currency must use an uppercase ISO-style code")


@dataclass(frozen=True)
class PriceObservation:
    security: Security
    trading_date: date
    close: Decimal
    provenance: Provenance
    adjusted_close: Decimal | None = None

    def __post_init__(self) -> None:
        if self.close < 0:
            raise ValueError("close cannot be negative")
        if self.adjusted_close is not None and self.adjusted_close < 0:
            raise ValueError("adjusted_close cannot be negative")
        if self.provenance.as_of != self.trading_date:
            raise ValueError("price provenance as_of must match trading_date")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def observations_are_ordered(observations: Iterable[PriceObservation]) -> bool:
    dates = [item.trading_date for item in observations]
    return dates == sorted(set(dates))
