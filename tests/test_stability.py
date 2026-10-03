from datetime import date

from fastapi.testclient import TestClient

from stock_analyzer.api import create_app
from stock_analyzer.config import Settings
from stock_analyzer.providers import make_fixture_provider


def test_fixture_provenance_is_deterministic() -> None:
    first = make_fixture_provider().get_prices("ASET", date(2024, 1, 1), date(2024, 1, 5))
    second = make_fixture_provider().get_prices("ASET", date(2024, 1, 1), date(2024, 1, 5))
    assert first == second


def test_invalid_request_id_is_replaced() -> None:
    response = TestClient(create_app()).get(
        "/api/v1/securities/ASET/prices?start=2024-01-01&end=2024-01-03",
        headers={"x-request-id": "not-a-uuid"},
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "not-a-uuid"


def test_limit_is_bounded() -> None:
    client = TestClient(create_app(settings=Settings(max_price_points=2)))
    response = client.get("/api/v1/securities/ASET/prices?start=2024-01-01&end=2024-01-05&limit=3")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_limit"


def test_provider_failure_is_not_leaked() -> None:
    class BrokenProvider:
        name = "broken"

        def get_security(self, symbol):
            raise RuntimeError("internal credentials leaked")

        def get_prices(self, symbol, start, end):
            raise RuntimeError("internal credentials leaked")

    response = TestClient(create_app(BrokenProvider())).get(
        "/api/v1/securities/ASET/prices?start=2024-01-01&end=2024-01-03"
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_unavailable"
    assert "credentials" not in response.text
