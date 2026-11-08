from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from prometheus_client import Gauge
from sqlalchemy import text

from ruletwin.db.database import Database


@dataclass(frozen=True, slots=True)
class OperationalSnapshot:
    outbox_ready: int
    outbox_delayed: int
    outbox_leased: int
    outbox_failed: int
    oldest_ready_age_seconds: float
    simulations_running: int
    stale_simulation_runs: int


OperationalSnapshotProbe = Callable[[], Awaitable[OperationalSnapshot]]

SNAPSHOT_SUCCESS = Gauge(
    "ruletwin_operational_snapshot_success",
    "Whether the latest database-backed operational snapshot succeeded",
)
DATABASE_READY = Gauge(
    "ruletwin_database_ready",
    "Whether the database was reachable during the latest operational snapshot",
)
SNAPSHOT_LAST_SUCCESS = Gauge(
    "ruletwin_operational_snapshot_last_success_unixtime",
    "Unix timestamp of the latest successful operational snapshot",
)
OUTBOX_READY = Gauge(
    "ruletwin_outbox_ready_events",
    "Outbox events ready for a worker to claim",
)
OUTBOX_DELAYED = Gauge(
    "ruletwin_outbox_delayed_events",
    "Pending outbox events delayed until a future retry time",
)
OUTBOX_LEASED = Gauge(
    "ruletwin_outbox_leased_events",
    "Pending outbox events with an active worker lease",
)
OUTBOX_FAILED = Gauge(
    "ruletwin_outbox_failed_events",
    "Outbox events that exhausted processing attempts",
)
OUTBOX_OLDEST_READY_AGE = Gauge(
    "ruletwin_outbox_oldest_ready_age_seconds",
    "Age in seconds of the oldest outbox event ready for processing",
)
SIMULATIONS_RUNNING = Gauge(
    "ruletwin_simulations_running",
    "Simulations currently in the running state",
)
STALE_SIMULATION_RUNS = Gauge(
    "ruletwin_stale_simulation_runs",
    "Running simulation attempts whose heartbeat is stale",
)

_SNAPSHOT_SQL = text(
    """
    SELECT
        (SELECT count(*) FROM outbox_events
         WHERE status = 'pending' AND available_at <= now()
           AND (leased_until IS NULL OR leased_until < now())) AS outbox_ready,
        (SELECT count(*) FROM outbox_events
         WHERE status = 'pending' AND available_at > now()) AS outbox_delayed,
        (SELECT count(*) FROM outbox_events
         WHERE status = 'pending' AND leased_until >= now()) AS outbox_leased,
        (SELECT count(*) FROM outbox_events
         WHERE status = 'failed') AS outbox_failed,
        COALESCE((SELECT EXTRACT(EPOCH FROM (now() - min(available_at)))
                  FROM outbox_events
                  WHERE status = 'pending' AND available_at <= now()
                    AND (leased_until IS NULL OR leased_until < now())), 0)
            AS oldest_ready_age_seconds,
        (SELECT count(*) FROM simulations WHERE status = 'running') AS simulations_running,
        (SELECT count(*) FROM simulation_runs
         WHERE status = 'running'
           AND heartbeat_at < now() - make_interval(secs => :stale_after_seconds))
            AS stale_simulation_runs
    """
)


async def read_operational_snapshot(
    database: Database, *, stale_after_seconds: int
) -> OperationalSnapshot:
    async with database.session() as session:
        result = await session.execute(
            _SNAPSHOT_SQL,
            {"stale_after_seconds": stale_after_seconds},
        )
        row = result.mappings().one()
    return OperationalSnapshot(
        outbox_ready=int(row["outbox_ready"]),
        outbox_delayed=int(row["outbox_delayed"]),
        outbox_leased=int(row["outbox_leased"]),
        outbox_failed=int(row["outbox_failed"]),
        oldest_ready_age_seconds=float(row["oldest_ready_age_seconds"]),
        simulations_running=int(row["simulations_running"]),
        stale_simulation_runs=int(row["stale_simulation_runs"]),
    )


def publish_operational_snapshot(snapshot: OperationalSnapshot) -> None:
    OUTBOX_READY.set(snapshot.outbox_ready)
    OUTBOX_DELAYED.set(snapshot.outbox_delayed)
    OUTBOX_LEASED.set(snapshot.outbox_leased)
    OUTBOX_FAILED.set(snapshot.outbox_failed)
    OUTBOX_OLDEST_READY_AGE.set(snapshot.oldest_ready_age_seconds)
    SIMULATIONS_RUNNING.set(snapshot.simulations_running)
    STALE_SIMULATION_RUNS.set(snapshot.stale_simulation_runs)
    DATABASE_READY.set(1)
    SNAPSHOT_SUCCESS.set(1)
    SNAPSHOT_LAST_SUCCESS.set(datetime.now(UTC).timestamp())


def publish_operational_snapshot_failure() -> None:
    DATABASE_READY.set(0)
    SNAPSHOT_SUCCESS.set(0)
