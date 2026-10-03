from fastapi.testclient import TestClient

from stock_analyzer.api import create_app
from stock_analyzer.config import Settings


def test_security_headers_are_present() -> None:
    client = TestClient(create_app(settings=Settings(environment="production")))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert "max-age=31536000" in response.headers["strict-transport-security"]


def test_untrusted_host_is_rejected() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health", headers={"host": "attacker.example"})
    assert response.status_code == 400


def test_cors_is_disabled_by_default() -> None:
    response = TestClient(create_app()).get("/api/v1/health", headers={"origin": "https://attacker.example"})
    assert "access-control-allow-origin" not in response.headers
