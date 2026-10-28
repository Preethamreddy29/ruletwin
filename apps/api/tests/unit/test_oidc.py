import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from ruletwin.api.auth import OidcTokenVerifier
from ruletwin.api.problems import ProblemError
from ruletwin.config import Settings


def oidc_settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql://localhost/ruletwin_test",
        auth_mode="oidc",
        oidc_issuer="https://identity.example/",
        oidc_audience="ruletwin-api",
        oidc_jwks_url="https://identity.example/.well-known/jwks.json",
    )


def key_pair(key_id: str) -> tuple[Any, dict[str, Any]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk.update({"kid": key_id, "alg": "RS256", "use": "sig"})
    return private_key, public_jwk


def oidc_token(
    settings: Settings,
    private_key: Any,
    key_id: str,
    *,
    issuer: str | None = None,
    audience: str | None = None,
    tenant_id: str | None = None,
    subject: str = "provider|pilot-user",
    expired: bool = False,
    excessive_lifetime: bool = False,
) -> str:
    now = datetime.now(UTC)
    claims = {
        "iss": issuer or settings.oidc_issuer,
        "aud": audience or settings.oidc_audience,
        "sub": subject,
        settings.oidc_tenant_claim: tenant_id or str(uuid.uuid4()),
        "iat": now - timedelta(minutes=2),
        "exp": (
            now - timedelta(minutes=1)
            if expired
            else now + timedelta(hours=2)
            if excessive_lifetime
            else now + timedelta(minutes=5)
        ),
    }
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": key_id})


@pytest.mark.asyncio
async def test_oidc_token_is_verified_and_jwks_is_cached() -> None:
    settings = oidc_settings()
    private_key, public_jwk = key_pair("pilot-key")
    tenant_id = uuid.uuid4()
    loads = 0

    async def load() -> dict[str, Any]:
        nonlocal loads
        loads += 1
        return {"keys": [public_jwk]}

    verifier = OidcTokenVerifier(settings, load)
    token = oidc_token(settings, private_key, "pilot-key", tenant_id=str(tenant_id))
    first = await verifier.verify(token)
    second = await verifier.verify(token)

    assert first == second
    assert first.oidc_subject == "provider|pilot-user"
    assert first.tenant_id == tenant_id
    assert first.actor_id is None
    assert loads == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation", ["issuer", "audience", "expired", "lifetime", "tenant", "subject"]
)
async def test_oidc_invalid_claims_fail_closed(mutation: str) -> None:
    settings = oidc_settings()
    private_key, public_jwk = key_pair("pilot-key")

    async def load() -> dict[str, Any]:
        return {"keys": [public_jwk]}

    token = oidc_token(
        settings,
        private_key,
        "pilot-key",
        issuer="https://wrong.example/" if mutation == "issuer" else None,
        audience="wrong-api" if mutation == "audience" else None,
        tenant_id="not-a-uuid" if mutation == "tenant" else None,
        subject="" if mutation == "subject" else "provider|pilot-user",
        expired=mutation == "expired",
        excessive_lifetime=mutation == "lifetime",
    )
    with pytest.raises(ProblemError, match="valid short-lived bearer token"):
        await OidcTokenVerifier(settings, load).verify(token)


@pytest.mark.asyncio
async def test_oidc_reloads_jwks_when_a_signing_key_rotates() -> None:
    settings = oidc_settings()
    old_private, old_public = key_pair("rotating-key")
    new_private, new_public = key_pair("rotating-key")
    loads = 0

    async def load() -> dict[str, Any]:
        nonlocal loads
        loads += 1
        return {"keys": [old_public if loads == 1 else new_public]}

    verifier = OidcTokenVerifier(settings, load)
    assert (await verifier.verify(oidc_token(settings, old_private, "rotating-key"))).oidc_subject
    assert (await verifier.verify(oidc_token(settings, new_private, "rotating-key"))).oidc_subject
    assert loads == 2


@pytest.mark.asyncio
async def test_oidc_rejects_unsupported_algorithm_and_unavailable_jwks() -> None:
    settings = oidc_settings()

    async def unavailable() -> dict[str, Any]:
        return {"keys": []}

    unsupported = jwt.encode(
        {"sub": "provider|pilot-user"},
        "not-used-for-verification-0000000000000000",
        algorithm="HS256",
        headers={"kid": "symmetric-key"},
    )
    with pytest.raises(ProblemError, match="valid short-lived bearer token"):
        await OidcTokenVerifier(settings, unavailable).verify(unsupported)
    private_key, _ = key_pair("pilot-key")
    with pytest.raises(ProblemError) as failure:
        await OidcTokenVerifier(settings, unavailable).verify(
            oidc_token(settings, private_key, "pilot-key")
        )
    assert failure.value.status == 503
