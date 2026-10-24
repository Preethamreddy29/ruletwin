import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import text

from ruletwin.api.problems import ProblemError
from ruletwin.config import Settings
from ruletwin.db.database import Database

bearer = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


@dataclass(frozen=True)
class Identity:
    actor_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: str
    tenant_slug: str
    tenant_display_name: str
    roles: frozenset[str]


def issue_token(settings: Settings, actor_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "sub": str(actor_id),
            "tenant_id": str(tenant_id),
            "iat": now,
            "exp": now + timedelta(seconds=settings.jwt_ttl_seconds),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_token(settings: Settings, token: str) -> tuple[uuid.UUID, uuid.UUID]:
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "tenant_id"]},
        )
        return uuid.UUID(str(claims["sub"])), uuid.UUID(str(claims["tenant_id"]))
    except (InvalidTokenError, ValueError, KeyError) as exc:
        raise ProblemError(
            401,
            "Authentication required",
            "A valid short-lived bearer token is required.",
            "authentication-required",
        ) from exc


async def authenticated_identity(request: Request, credentials: Credentials) -> Identity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ProblemError(
            401,
            "Authentication required",
            "A valid short-lived bearer token is required.",
            "authentication-required",
        )
    settings: Settings = request.app.state.settings
    actor_id, tenant_id = decode_token(settings, credentials.credentials)
    database: Database = request.app.state.database
    async with database.session() as session:
        rows = (
            (
                await session.execute(
                    text(
                        """
                        SELECT u.email, u.display_name, t.slug AS tenant_slug,
                               t.display_name AS tenant_display_name, utr.role_code
                        FROM users u
                        JOIN user_tenant_roles utr ON utr.user_id=u.id
                        JOIN tenants t ON t.id=utr.tenant_id
                        WHERE u.id=:actor_id AND t.id=:tenant_id
                        ORDER BY utr.role_code
                        """
                    ),
                    {"actor_id": actor_id, "tenant_id": tenant_id},
                )
            )
            .mappings()
            .all()
        )
    if not rows:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    first = rows[0]
    return Identity(
        actor_id=actor_id,
        tenant_id=tenant_id,
        email=first["email"],
        display_name=first["display_name"],
        tenant_slug=first["tenant_slug"],
        tenant_display_name=first["tenant_display_name"],
        roles=frozenset(row["role_code"] for row in rows),
    )


def require_roles(*allowed: str) -> Any:
    async def dependency(
        identity: Annotated[Identity, Depends(authenticated_identity)],
    ) -> Identity:
        if identity.roles.isdisjoint(allowed):
            raise ProblemError(404, "Not found", "Resource not found.", "not-found")
        return identity

    return dependency
