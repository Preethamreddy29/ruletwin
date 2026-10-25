from httpx import ASGITransport, AsyncClient

from ruletwin.api.app import create_app
from ruletwin.api.auth import decode_token
from ruletwin.config import Settings
from ruletwin.scenario import AUTHOR_ID, TENANT_ID


async def test_development_identities_and_signed_token_are_explicitly_synthetic(
    ready_client: AsyncClient, settings: Settings
) -> None:
    identities = await ready_client.get("/v1/dev/identities")
    assert identities.status_code == 200
    assert len(identities.json()["items"]) == 8
    assert {item["tenant"] for item in identities.json()["items"]} == {
        "NovaBill Sandbox",
        "Brightline Sandbox",
    }

    response = await ready_client.post("/v1/dev/token", json={"identity_key": "novabill-analyst"})
    assert response.status_code == 200
    assert decode_token(settings, response.json()["access_token"]) == (AUTHOR_ID, TENANT_ID)


async def test_development_identity_endpoints_are_hidden_outside_dev() -> None:
    settings = Settings(
        environment="staging",
        database_url="postgresql+psycopg://test:test@localhost/ruletwin_test",
        log_level="CRITICAL",
        auth_mode="oidc",
        oidc_issuer="https://identity.example/",
        oidc_audience="ruletwin-api",
        oidc_jwks_url="https://identity.example/.well-known/jwks.json",
    )

    async def ready() -> bool:
        return True

    app = create_app(settings, readiness_probe=ready)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        identities = await client.get("/v1/dev/identities")
        token = await client.post("/v1/dev/token", json={"identity_key": "novabill-analyst"})
    assert identities.status_code == token.status_code == 404
