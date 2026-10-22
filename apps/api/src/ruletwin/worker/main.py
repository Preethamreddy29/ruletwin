import asyncio
import logging
import os
import socket

from sqlalchemy import text

from ruletwin.application.vertical_slice import process_simulation_event
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
            try:
                async with database.session() as session, session.begin():
                    outcome = await process_simulation_event(session, event, worker_id=worker_id)
                LOGGER.info(
                    "outbox_event_processed",
                    extra={"request_id": str(event.id), "trace_id": str(event.id)},
                )
                if outcome == "failed":
                    LOGGER.error(
                        "outbox_event_unsupported",
                        extra={"request_id": str(event.id), "trace_id": str(event.id)},
                    )
            except Exception as exc:
                LOGGER.exception(
                    "outbox_event_processing_failed",
                    extra={"request_id": str(event.id), "trace_id": str(event.id)},
                )
                async with database.session() as session, session.begin():
                    await session.execute(
                        text(
                            """
                            UPDATE outbox_events
                            SET leased_until=NULL, lease_owner=NULL, last_error=:error,
                                available_at=now() + interval '2 seconds'
                            WHERE id=:id AND status='pending'
                            """
                        ),
                        {"id": event.id, "error": str(exc)[:1000]},
                    )
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
