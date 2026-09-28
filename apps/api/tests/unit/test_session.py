from httpx import ASGITransport, AsyncClient

from ruletwin.api.app import create_app
from ruletwin.config import Settings


async def test_development_session_is_explicitly_synthetic(ready_client: AsyncClient) -> None:
    response = await ready_client.get("/v1/dev/session")
    assert response.status_code == 200
    assert response.json()["synthetic"] is True
    assert response.json()["tenant"]["slug"] == "novabill-sandbox"


async def test_development_session_is_hidden_outside_dev() -> None:
    settings = Settings(
        environment="staging",
        database_url="postgresql+psycopg://test:test@localhost/ruletwin_test",
        log_level="CRITICAL",
    )

    async def ready() -> bool:
        return True

    app = create_app(settings, readiness_probe=ready)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/dev/session")
    assert response.status_code == 404
