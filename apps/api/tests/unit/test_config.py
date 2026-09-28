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
        Settings(environment="test", database_url="sqlite:///unsafe.db")


def test_cors_origins_are_trimmed() -> None:
    settings = Settings(
        environment="test",
        database_url="postgresql://localhost/ruletwin_test",
        cors_origins="http://one.example, http://two.example ",
    )
    assert settings.parsed_cors_origins == ["http://one.example", "http://two.example"]
