from fastapi.testclient import TestClient

from stock_analyzer.api import app


client = TestClient(app)


def test_health_and_readiness() -> None:
    assert client.get("/api/v1/health").json()["status"] == "healthy"
    assert client.get("/api/v1/readiness").json() == {"status": "ready", "provider": "fixture"}


def test_prices_are_versioned_and_include_request_id() -> None:
    response = client.get("/api/v1/securities/ASET/prices?start=2024-01-01&end=2024-01-03")
    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.json()[0]["source"].startswith("fixture://prices/ASET/")


def test_invalid_period_returns_structured_error() -> None:
    response = client.get("/api/v1/securities/ASET/prices?start=2024-01-05&end=2024-01-01")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_period"


def test_unknown_security_returns_not_found() -> None:
    response = client.get("/api/v1/securities/NOPE/prices?start=2024-01-01&end=2024-01-03")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "security_not_found"
