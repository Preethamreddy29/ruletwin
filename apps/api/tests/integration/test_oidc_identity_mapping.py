import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import text

from ruletwin.api.app import create_app
from ruletwin.api.auth import OidcTokenVerifier
from ruletwin.config import Settings
from ruletwin.db.database import Database
from ruletwin.provision_oidc import provision_oidc_subject
from ruletwin.scenario import APPROVER_ID, AUTHOR_ID, SECOND_TENANT_ID, TENANT_ID
from ruletwin.seed import seed


@pytest.mark.integration
async def test_oidc_subject_maps_to_database_roles_and_tenant_membership() -> None:
    url = os.environ.get("RULETWIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("RULETWIN_TEST_DATABASE_URL is not configured")
    await seed("ruletwin-dev-v1")
    subject = f"provider|{uuid.uuid4()}"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk: dict[str, Any] = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk.update({"kid": "integration-key", "alg": "RS256", "use": "sig"})
    settings = Settings(
        environment="test",
        database_url=url,
        auth_mode="oidc",
        oidc_issuer="https://identity.example/",
        oidc_audience="ruletwin-api",
        oidc_jwks_url="https://identity.example/.well-known/jwks.json",
        log_level="CRITICAL",
    )

    async def load() -> dict[str, Any]:
        return {"keys": [public_jwk]}

    def token(token_subject: str, tenant_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "iss": settings.oidc_issuer,
                "aud": settings.oidc_audience,
                "sub": token_subject,
                settings.oidc_tenant_claim: str(tenant_id),
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            private_key,
            algorithm="RS256",
            headers={"kid": "integration-key"},
        )

    database = Database(url)
    try:
        changed = await provision_oidc_subject(
            url,
            identity_key="novabill-analyst",
            subject=subject,
            approved_by_identity_key="novabill-approver",
        )
        repeated = await provision_oidc_subject(
            url,
            identity_key="novabill-analyst",
            subject=subject,
            approved_by_identity_key="novabill-approver",
        )
        assert changed is True
        assert repeated is False

        async with database.session() as session:
            provision_event = (
                (
                    await session.execute(
                        text(
                            """
                            SELECT actor_id, metadata FROM audit_events
                            WHERE tenant_id=:tenant_id
                              AND action='identity.oidc_subject.provisioned'
                              AND object_id=:object_id
                            ORDER BY created_at DESC LIMIT 1
                            """
                        ),
                        {"tenant_id": TENANT_ID, "object_id": AUTHOR_ID},
                    )
                )
                .mappings()
                .one()
            )
        assert provision_event["actor_id"] == APPROVER_ID
        assert provision_event["metadata"]["subject_digest"].startswith("sha256:")
        assert subject not in json.dumps(provision_event["metadata"])

        app = create_app(settings)
        app.state.token_verifier = OidcTokenVerifier(settings, load)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            authorized = await client.get(
                "/v1/session",
                headers={"Authorization": f"Bearer {token(subject, TENANT_ID)}"},
            )
            wrong_tenant = await client.get(
                "/v1/session",
                headers={"Authorization": f"Bearer {token(subject, SECOND_TENANT_ID)}"},
            )
            unknown_subject = await client.get(
                "/v1/session",
                headers={"Authorization": f"Bearer {token('provider|unknown', TENANT_ID)}"},
            )

        assert authorized.status_code == 200
        assert authorized.json()["user"]["id"] == str(AUTHOR_ID)
        assert authorized.json()["tenant"]["id"] == str(TENANT_ID)
        assert authorized.json()["roles"] == ["author"]
        assert authorized.json()["synthetic"] is False
        assert wrong_tenant.status_code == unknown_subject.status_code == 404
        assert wrong_tenant.json()["detail"] == unknown_subject.json()["detail"]
    finally:
        async with database.session() as session, session.begin():
            await session.execute(
                text("UPDATE users SET oidc_subject=NULL WHERE id=:id"),
                {"id": AUTHOR_ID},
            )
            await session.execute(
                text(
                    """
                    DELETE FROM audit_events
                    WHERE tenant_id=:tenant_id
                      AND action='identity.oidc_subject.provisioned'
                      AND object_id=:object_id
                    """
                ),
                {"tenant_id": TENANT_ID, "object_id": AUTHOR_ID},
            )
        await database.dispose()
