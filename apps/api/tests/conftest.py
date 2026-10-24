import asyncio
import sys
from collections.abc import AsyncIterator, Callable

import pytest
from httpx import ASGITransport, AsyncClient

from ruletwin.api.app import create_app
from ruletwin.config import Settings


def pytest_asyncio_loop_factories() -> dict[str, Callable[[], asyncio.AbstractEventLoop]]:
    if sys.platform == "win32":
        return {"windows-selector": asyncio.SelectorEventLoop}
    return {"default": asyncio.new_event_loop}


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql+psycopg://test:test@localhost/ruletwin_test",
        log_level="CRITICAL",
        jwt_secret="test-only-ruletwin-jwt-secret-000000000000",
    )


@pytest.fixture
async def ready_client(settings: Settings) -> AsyncIterator[AsyncClient]:
    async def ready() -> bool:
        return True

    app = create_app(settings, readiness_probe=ready)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
