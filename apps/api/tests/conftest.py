import asyncio
import sys
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from ruletwin.api.app import create_app
from ruletwin.config import Settings


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    if sys.platform == "win32":
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql+psycopg://test:test@localhost/ruletwin_test",
        log_level="CRITICAL",
    )


@pytest.fixture
async def ready_client(settings: Settings) -> AsyncIterator[AsyncClient]:
    async def ready() -> bool:
        return True

    app = create_app(settings, readiness_probe=ready)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
