import asyncio
from uuid import UUID

from httpx import AsyncClient

from ruletwin.api.app import create_app
from ruletwin.config import Settings


async def test_liveness_and_readiness(ready_client: AsyncClient) -> None:
    live = await ready_client.get("/health/live")
    ready = await ready_client.get("/health/ready")
    assert live.status_code == 200
    assert live.json() == {"status": "alive", "service": "ruletwin-api"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "database": "reachable"}


async def test_unhealthy_database_returns_problem(settings: Settings) -> None:
    async def unavailable() -> bool:
        return False

    app = create_app(settings, readiness_probe=unavailable)
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "not-ready"


async def test_readiness_probe_timeout_fails_closed(settings: Settings) -> None:
    settings.readiness_timeout_seconds = 0.01

    async def too_slow() -> bool:
        await asyncio.sleep(0.02)
        return True

    app = create_app(settings, readiness_probe=too_slow)
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["code"] == "not-ready"


async def test_request_context_is_returned(ready_client: AsyncClient) -> None:
    response = await ready_client.get("/version", headers={"X-Correlation-ID": "invalid"})
    assert response.status_code == 200
    assert UUID(response.headers["X-Correlation-ID"])
    assert response.headers["X-Trace-ID"]


async def test_valid_correlation_id_is_preserved(ready_client: AsyncClient) -> None:
    correlation_id = "e7c82856-fb34-4d66-8139-bcad9c579d79"
    response = await ready_client.get("/version", headers={"X-Correlation-ID": correlation_id})
    assert response.headers["X-Correlation-ID"] == correlation_id


async def test_missing_route_uses_stable_problem_contract(ready_client: AsyncClient) -> None:
    response = await ready_client.get("/does-not-exist")
    body = response.json()
    assert response.status_code == 404
    assert body["code"] == "not-found"
    assert body["correlation_id"] == response.headers["X-Correlation-ID"]
