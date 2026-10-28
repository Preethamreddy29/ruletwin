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


def retry_delay_seconds(attempt: int, *, base_seconds: int, max_seconds: int) -> int:
    return int(min(max_seconds, base_seconds * (2 ** max(0, attempt - 1))))


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
                    max_attempts=settings.worker_max_attempts,
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
                    async with asyncio.timeout(settings.worker_execution_timeout_seconds):
                        outcome = await process_simulation_event(
                            session, event, worker_id=worker_id
                        )
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
                    if event.attempts >= settings.worker_max_attempts:
                        await session.execute(
                            text(
                                """
                                UPDATE outbox_events
                                SET status='failed', leased_until=NULL, lease_owner=NULL,
                                    last_error=:error
                                WHERE id=:id AND status='pending'
                                """
                            ),
                            {"id": event.id, "error": str(exc)[:1000]},
                        )
                        await session.execute(
                            text(
                                """
                                UPDATE simulations SET status='failed', version=version+1
                                WHERE id=:simulation_id
                                  AND tenant_id=:tenant_id
                                  AND status IN ('requested','queued','running')
                                """
                            ),
                            {
                                "simulation_id": event.aggregate_id,
                                "tenant_id": event.tenant_id,
                            },
                        )
                    else:
                        delay = retry_delay_seconds(
                            event.attempts,
                            base_seconds=settings.worker_retry_base_seconds,
                            max_seconds=settings.worker_retry_max_seconds,
                        )
                        await session.execute(
                            text(
                                """
                                UPDATE outbox_events
                                SET leased_until=NULL, lease_owner=NULL, last_error=:error,
                                    available_at=now() + make_interval(secs => :delay)
                                WHERE id=:id AND status='pending'
                                """
                            ),
                            {"id": event.id, "error": str(exc)[:1000], "delay": delay},
                        )
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
