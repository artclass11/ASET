from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from stock_analyzer.analytics import annualized_volatility, maximum_drawdown, simple_return
from stock_analyzer.domain import PriceObservation, Provenance, Security
from stock_analyzer.providers import make_fixture_provider


def test_fixture_provider_returns_provenance_rich_prices() -> None:
    observations = make_fixture_provider().get_prices("aset", date(2024, 1, 1), date(2024, 1, 5))
    assert len(observations) == 5
    assert observations[0].provenance.provider == "fixture"
    assert observations[-1].provenance.as_of == date(2024, 1, 5)


def test_metrics_are_deterministic() -> None:
    observations = make_fixture_provider().get_prices("ASET", date(2024, 1, 1), date(2024, 1, 5))
    assert simple_return(observations).value == pytest.approx(0.10)
    assert maximum_drawdown(observations).value == pytest.approx(-1 / 102, rel=1e-6)
    assert annualized_volatility(observations).value > 0


def test_domain_rejects_naive_provenance() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Provenance("fixture", "fixture://x", datetime(2024, 1, 1), date(2024, 1, 1))


def test_metrics_reject_duplicate_dates() -> None:
    security_provenance = Provenance("fixture", "fixture://security", datetime.now(timezone.utc), date(2024, 1, 1))
    security = Security("X", "Example", "NYSE", "USD", security_provenance)
    first = PriceObservation(security, date(2024, 1, 1), Decimal("10"), Provenance("fixture", "fixture://1", datetime.now(timezone.utc), date(2024, 1, 1)))
    duplicate = PriceObservation(security, date(2024, 1, 1), Decimal("11"), Provenance("fixture", "fixture://2", datetime.now(timezone.utc), date(2024, 1, 1)))
    with pytest.raises(ValueError, match="unique dates"):
        simple_return((first, duplicate))
