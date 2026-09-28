from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
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
    version: str = "0.1.0-dev-foundation"
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

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
