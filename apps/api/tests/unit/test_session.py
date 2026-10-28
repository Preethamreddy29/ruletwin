import uuid
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from ruletwin.api.app import create_app
from ruletwin.api.auth import Identity, decode_token
from ruletwin.api.problems import ProblemError
from ruletwin.api.vertical_slice import CreateDataset, post_dataset
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


async def test_dataset_event_limit_fails_before_database_access(
    settings: Settings,
) -> None:
    app = SimpleNamespace(state=SimpleNamespace(settings=settings))
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/replay-datasets",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 123),
            "app": app,
        }
    )
    request.state.request_id = str(uuid.uuid4())
    identity = Identity(
        actor_id=AUTHOR_ID,
        tenant_id=TENANT_ID,
        email="analyst@novabill.example",
        display_name="NovaBill Analyst",
        tenant_slug="novabill",
        tenant_display_name="NovaBill Sandbox",
        roles=frozenset({"author"}),
    )
    body = CreateDataset(
        tenant_id=TENANT_ID,
        seed=1,
        generator_version="rounding-events-v1",
        event_schema_version="business-event-v1",
        event_count=10001,
    )

    with pytest.raises(ProblemError) as exceeded:
        await post_dataset(body, request, identity, "dataset-limit-test-0001")
    assert exceeded.value.status == 413
    assert exceeded.value.code == "dataset-limit-exceeded"
