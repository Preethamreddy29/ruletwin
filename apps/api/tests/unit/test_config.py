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


def test_resource_limits_reject_unsafe_configuration() -> None:
    with pytest.raises(ValidationError, match="retry base"):
        Settings(
            environment="test",
            database_url="postgresql://localhost/ruletwin_test",
            jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
            worker_retry_base_seconds=10,
            worker_retry_max_seconds=5,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            database_url="postgresql://localhost/ruletwin_test",
            jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
            worker_concurrency=2,
        )


def test_worker_concurrency_accepts_compose_environment_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RULETWIN_ENVIRONMENT", "test")
    monkeypatch.setenv("RULETWIN_DATABASE_URL", "postgresql://localhost/ruletwin_test")
    monkeypatch.setenv("RULETWIN_JWT_SECRET", "test-only-ruletwin-jwt-secret-000000000000")
    monkeypatch.setenv("RULETWIN_WORKER_CONCURRENCY", "1")

    assert Settings(_env_file=None).worker_concurrency == 1  # type: ignore[call-arg]


def test_configuration_loads_mounted_secret_files(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("RULETWIN_DATABASE_URL", raising=False)
    monkeypatch.delenv("RULETWIN_JWT_SECRET", raising=False)
    database_file = tmp_path / "database-url"
    jwt_file = tmp_path / "jwt-secret"
    database_file.write_text("postgresql://localhost/ruletwin_test\n", encoding="utf-8")
    jwt_file.write_text("test-only-mounted-jwt-secret-000000000000\n", encoding="utf-8")

    settings = Settings(
        environment="test",
        database_url_file=str(database_file.resolve()),
        jwt_secret_file=str(jwt_file.resolve()),
        _env_file=None,
    )

    assert settings.database_url == "postgresql://localhost/ruletwin_test"
    assert settings.jwt_secret == "test-only-mounted-jwt-secret-000000000000"


def test_configuration_rejects_ambiguous_or_relative_secret_files(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("RULETWIN_DATABASE_URL", raising=False)
    monkeypatch.delenv("RULETWIN_JWT_SECRET", raising=False)
    database_file = tmp_path / "database-url"
    database_file.write_text("postgresql://localhost/ruletwin_test", encoding="utf-8")

    with pytest.raises(ValidationError, match="configure only one"):
        Settings(
            environment="test",
            database_url="postgresql://localhost/ruletwin_test",
            database_url_file=str(database_file.resolve()),
            jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
            _env_file=None,
        )
    with pytest.raises(ValidationError, match="absolute path"):
        Settings(
            environment="test",
            database_url_file="relative/database-url",
            jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
            _env_file=None,
        )
