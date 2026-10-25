import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Protocol

import httpx
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidSignatureError, InvalidTokenError, PyJWK
from sqlalchemy import text

from ruletwin.api.problems import ProblemError
from ruletwin.config import Settings
from ruletwin.db.database import Database

bearer = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
JwksLoader = Callable[[], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Identity:
    actor_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: str
    tenant_slug: str
    tenant_display_name: str
    roles: frozenset[str]


@dataclass(frozen=True)
class TokenPrincipal:
    tenant_id: uuid.UUID
    actor_id: uuid.UUID | None = None
    oidc_subject: str | None = None


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> TokenPrincipal: ...


def _authentication_error() -> ProblemError:
    return ProblemError(
        401,
        "Authentication required",
        "A valid short-lived bearer token is required.",
        "authentication-required",
    )


def issue_token(settings: Settings, actor_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    if settings.auth_mode != "development" or settings.jwt_secret is None:
        raise RuntimeError("Development tokens are disabled.")
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
    if settings.auth_mode != "development" or settings.jwt_secret is None:
        raise _authentication_error()
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
        raise _authentication_error() from exc


class DevelopmentTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def verify(self, token: str) -> TokenPrincipal:
        actor_id, tenant_id = decode_token(self._settings, token)
        return TokenPrincipal(actor_id=actor_id, tenant_id=tenant_id)


class OidcTokenVerifier:
    def __init__(self, settings: Settings, loader: JwksLoader | None = None) -> None:
        if settings.auth_mode != "oidc":
            raise ValueError("OIDC verifier requires auth_mode=oidc")
        self._settings = settings
        self._loader = loader or self._fetch_jwks
        self._keys: dict[str, PyJWK] = {}
        self._cache_expires_at = 0.0
        self._forced_refresh_allowed_at = 0.0
        self._lock = asyncio.Lock()

    async def _fetch_jwks(self) -> dict[str, Any]:
        assert self._settings.oidc_jwks_url is not None
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.oidc_http_timeout_seconds,
                follow_redirects=False,
            ) as client:
                response = await client.get(
                    self._settings.oidc_jwks_url,
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                return payload
        except (httpx.HTTPError, ValueError) as exc:
            raise ProblemError(
                503,
                "Identity provider unavailable",
                "OIDC signing keys could not be loaded.",
                "identity-provider-unavailable",
            ) from exc

    async def _load_keys(self, *, force: bool = False) -> dict[str, PyJWK]:
        now = time.monotonic()
        if not force and self._keys and now < self._cache_expires_at:
            return self._keys
        if force and self._keys and now < self._forced_refresh_allowed_at:
            return self._keys
        async with self._lock:
            now = time.monotonic()
            if not force and self._keys and now < self._cache_expires_at:
                return self._keys
            if force and self._keys and now < self._forced_refresh_allowed_at:
                return self._keys
            try:
                payload = await self._loader()
                raw_keys = payload.get("keys")
                if not isinstance(raw_keys, list) or not 1 <= len(raw_keys) <= 20:
                    raise ValueError("JWKS must contain between 1 and 20 keys")
                parsed: dict[str, PyJWK] = {}
                for raw_key in raw_keys:
                    if not isinstance(raw_key, dict):
                        continue
                    key_id = raw_key.get("kid")
                    if (
                        isinstance(key_id, str)
                        and key_id
                        and raw_key.get("kty") == "RSA"
                        and raw_key.get("alg", "RS256") == "RS256"
                        and raw_key.get("use", "sig") == "sig"
                    ):
                        parsed[key_id] = PyJWK.from_dict(raw_key, algorithm="RS256")
                if not parsed:
                    raise ValueError("JWKS did not contain an RS256 signing key")
            except ProblemError:
                raise
            except (InvalidTokenError, ValueError, TypeError) as exc:
                raise ProblemError(
                    503,
                    "Identity provider unavailable",
                    "OIDC signing keys were invalid.",
                    "identity-provider-unavailable",
                ) from exc
            self._keys = parsed
            self._cache_expires_at = now + self._settings.oidc_jwks_cache_seconds
            if force:
                self._forced_refresh_allowed_at = (
                    now + self._settings.oidc_jwks_refresh_cooldown_seconds
                )
            return parsed

    async def _signing_key(self, key_id: str, *, force: bool = False) -> PyJWK:
        key = (await self._load_keys(force=force)).get(key_id)
        if key is None and not force:
            key = (await self._load_keys(force=True)).get(key_id)
        if key is None:
            raise _authentication_error()
        return key

    def _decode(self, token: str, key: PyJWK) -> TokenPrincipal:
        assert self._settings.oidc_issuer is not None
        assert self._settings.oidc_audience is not None
        tenant_claim = self._settings.oidc_tenant_claim
        claims: dict[str, Any] = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=self._settings.oidc_audience,
            issuer=self._settings.oidc_issuer,
            options={
                "require": ["exp", "iat", "iss", "aud", "sub", tenant_claim],
            },
        )
        subject = claims["sub"]
        if not isinstance(subject, str) or not 1 <= len(subject) <= 255:
            raise _authentication_error()
        issued_at = claims["iat"]
        expires_at = claims["exp"]
        if (
            isinstance(issued_at, bool)
            or isinstance(expires_at, bool)
            or not isinstance(issued_at, int | float)
            or not isinstance(expires_at, int | float)
            or expires_at - issued_at > self._settings.oidc_max_token_lifetime_seconds
        ):
            raise _authentication_error()
        return TokenPrincipal(
            oidc_subject=subject,
            tenant_id=uuid.UUID(str(claims[tenant_claim])),
        )

    async def verify(self, token: str) -> TokenPrincipal:
        try:
            header = jwt.get_unverified_header(token)
            key_id = header.get("kid")
            if header.get("alg") != "RS256" or not isinstance(key_id, str) or not key_id:
                raise _authentication_error()
            key = await self._signing_key(key_id)
            try:
                return self._decode(token, key)
            except InvalidSignatureError:
                return self._decode(token, await self._signing_key(key_id, force=True))
        except ProblemError:
            raise
        except (InvalidTokenError, ValueError, KeyError, TypeError) as exc:
            raise _authentication_error() from exc


def create_token_verifier(settings: Settings) -> TokenVerifier:
    if settings.auth_mode == "oidc":
        return OidcTokenVerifier(settings)
    return DevelopmentTokenVerifier(settings)


async def authenticated_identity(request: Request, credentials: Credentials) -> Identity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_error()
    verifier: TokenVerifier = request.app.state.token_verifier
    principal = await verifier.verify(credentials.credentials)
    database: Database = request.app.state.database
    if principal.actor_id is not None:
        identity_filter = "u.id=:identity_value"
        identity_value: uuid.UUID | str = principal.actor_id
    else:
        identity_filter = "u.oidc_subject=:identity_value"
        if principal.oidc_subject is None:
            raise _authentication_error()
        identity_value = principal.oidc_subject
    async with database.session() as session:
        rows = (
            (
                await session.execute(
                    text(
                        f"""
                        SELECT u.id, u.email, u.display_name, t.slug AS tenant_slug,
                               t.display_name AS tenant_display_name, utr.role_code
                        FROM users u
                        JOIN user_tenant_roles utr ON utr.user_id=u.id
                        JOIN tenants t ON t.id=utr.tenant_id
                        WHERE {identity_filter} AND t.id=:tenant_id
                        ORDER BY utr.role_code
                        """  # noqa: S608 -- identity_filter is selected from two static literals.
                    ),
                    {"identity_value": identity_value, "tenant_id": principal.tenant_id},
                )
            )
            .mappings()
            .all()
        )
    if not rows:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    first = rows[0]
    return Identity(
        actor_id=first["id"],
        tenant_id=principal.tenant_id,
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
