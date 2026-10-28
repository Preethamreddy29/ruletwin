import pytest
from pydantic import ValidationError

from ruletwin.config import Settings


def test_configuration_requires_environment_and_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RULETWIN_ENVIRONMENT", raising=False)
    monkeypatch.delenv("RULETWIN_DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_configuration_rejects_non_postgres_database() -> None:
    with pytest.raises(ValidationError, match="PostgreSQL"):
        Settings(
            environment="test",
            database_url="sqlite:///unsafe.db",
            jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
        )


def test_cors_origins_are_trimmed() -> None:
    settings = Settings(
        environment="test",
        database_url="postgresql://localhost/ruletwin_test",
        cors_origins="http://one.example, http://two.example ",
        jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
    )
    assert settings.parsed_cors_origins == ["http://one.example", "http://two.example"]


def test_development_authentication_is_rejected_outside_dev_or_test() -> None:
    with pytest.raises(ValidationError, match="development authentication"):
        Settings(
            environment="staging",
            database_url="postgresql://localhost/ruletwin",
            jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
        )


def test_oidc_configuration_is_required_and_https_only() -> None:
    with pytest.raises(ValidationError, match="OIDC configuration is missing"):
        Settings(
            environment="staging",
            database_url="postgresql://localhost/ruletwin",
            auth_mode="oidc",
        )
    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings(
            environment="staging",
            database_url="postgresql://localhost/ruletwin",
            auth_mode="oidc",
            oidc_issuer="http://identity.example",
            oidc_audience="ruletwin-api",
            oidc_jwks_url="http://identity.example/.well-known/jwks.json",
        )
