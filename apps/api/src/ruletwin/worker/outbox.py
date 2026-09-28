from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class ClaimedEvent:
    id: UUID
    tenant_id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    payload: dict[str, object]
    attempts: int
    leased_until: datetime


CLAIM_SQL = text(
    """
    WITH candidate AS (
        SELECT id
        FROM outbox_events
        WHERE status = 'pending'
          AND available_at <= now()
          AND (leased_until IS NULL OR leased_until < now())
        ORDER BY available_at, id
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    UPDATE outbox_events AS event
    SET leased_until = now() + make_interval(secs => :lease_seconds),
        lease_owner = :lease_owner,
        attempts = attempts + 1
    FROM candidate
    WHERE event.id = candidate.id
    RETURNING event.id, event.tenant_id, event.event_type, event.aggregate_type,
              event.aggregate_id, event.payload, event.attempts, event.leased_until
    """
)


async def claim_one(
    session: AsyncSession,
    *,
    lease_owner: str,
    lease_seconds: int,
) -> ClaimedEvent | None:
    result = await session.execute(
        CLAIM_SQL,
        {"lease_owner": lease_owner, "lease_seconds": lease_seconds},
    )
    row = result.mappings().one_or_none()
    if row is None:
        return None
    return ClaimedEvent(**dict(row))
