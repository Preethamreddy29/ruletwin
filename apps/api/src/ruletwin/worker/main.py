import asyncio
import logging
import os
import socket

from ruletwin.config import get_settings
from ruletwin.db.database import Database
from ruletwin.logging import configure_logging
from ruletwin.worker.outbox import claim_one

LOGGER = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    database = Database(settings.database_url)
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    LOGGER.info("worker_started", extra={"request_id": None, "trace_id": None})
    try:
        while True:
            async with database.session() as session, session.begin():
                event = await claim_one(
                    session,
                    lease_owner=worker_id,
                    lease_seconds=settings.worker_lease_seconds,
                )
            if event is None:
                LOGGER.info("worker_heartbeat", extra={"request_id": None, "trace_id": None})
                await asyncio.sleep(settings.worker_poll_seconds)
                continue
            LOGGER.info(
                "outbox_event_claimed",
                extra={"request_id": str(event.id), "trace_id": str(event.id)},
            )
            # Phase 2 proves safe claiming only. Product handlers begin in Phase 3.
            await asyncio.sleep(0)
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
