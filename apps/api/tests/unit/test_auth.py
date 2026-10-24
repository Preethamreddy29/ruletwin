import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from ruletwin.api.auth import decode_token, issue_token
from ruletwin.api.problems import ProblemError
from ruletwin.config import Settings


def test_short_lived_token_round_trip(settings: Settings) -> None:
    actor_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    assert decode_token(settings, issue_token(settings, actor_id, tenant_id)) == (
        actor_id,
        tenant_id,
    )


@pytest.mark.parametrize("mutation", ["secret", "issuer", "audience", "expired"])
def test_invalid_token_fails_closed(settings: Settings, mutation: str) -> None:
    now = datetime.now(UTC)
    claims = {
        "iss": "wrong" if mutation == "issuer" else settings.jwt_issuer,
        "aud": "wrong" if mutation == "audience" else settings.jwt_audience,
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "iat": now - timedelta(minutes=2),
        "exp": now - timedelta(minutes=1) if mutation == "expired" else now + timedelta(minutes=1),
    }
    secret = (
        "wrong-test-secret-000000000000000000000" if mutation == "secret" else settings.jwt_secret
    )
    token = jwt.encode(claims, secret, algorithm="HS256")
    with pytest.raises(ProblemError, match="valid short-lived bearer token"):
        decode_token(settings, token)
