from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated process configuration loaded exclusively from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RULETWIN_",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["dev", "test", "staging", "local-prod"]
    database_url: str = Field(min_length=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    service_name: str = "ruletwin-api"
    version: str = "0.3.0-alpha-authz"
    auth_mode: Literal["development", "oidc"] = "development"
    jwt_secret: str | None = Field(default=None, min_length=32)
    jwt_issuer: str = "ruletwin-local"
    jwt_audience: str = "ruletwin-api"
    jwt_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_tenant_claim: str = Field(default="tenant_id", min_length=1, max_length=200)
    oidc_jwks_cache_seconds: int = Field(default=300, ge=30, le=3600)
    oidc_jwks_refresh_cooldown_seconds: int = Field(default=10, ge=1, le=60)
    oidc_http_timeout_seconds: float = Field(default=3.0, gt=0, le=10)
    oidc_max_token_lifetime_seconds: int = Field(default=3600, ge=60, le=86400)
    synthetic_user_id: str = "4c542107-b2c6-5f9f-9bb8-832efd9b3dc2"
    synthetic_user_email: str = "analyst@novabill.example"
    readiness_timeout_seconds: float = Field(default=2.0, gt=0, le=10)
    worker_poll_seconds: float = Field(default=2.0, gt=0, le=60)
    worker_lease_seconds: int = Field(default=30, ge=5, le=300)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql+psycopg://", "postgresql://")):
            raise ValueError("database_url must use PostgreSQL with psycopg")
        return value

    @model_validator(mode="after")
    def validate_authentication_mode(self) -> "Settings":
        if self.auth_mode == "development":
            if self.environment not in {"dev", "test"}:
                raise ValueError("development authentication is allowed only in dev or test")
            if self.jwt_secret is None:
                raise ValueError("jwt_secret is required for development authentication")
            return self

        required = {
            "oidc_issuer": self.oidc_issuer,
            "oidc_audience": self.oidc_audience,
            "oidc_jwks_url": self.oidc_jwks_url,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"OIDC configuration is missing: {', '.join(missing)}")
        if self.environment != "test":
            issuer = self.oidc_issuer or ""
            jwks_url = self.oidc_jwks_url or ""
            if not issuer.startswith("https://"):
                raise ValueError("oidc_issuer must use HTTPS outside tests")
            if not jwks_url.startswith("https://"):
                raise ValueError("oidc_jwks_url must use HTTPS outside tests")
        return self

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
