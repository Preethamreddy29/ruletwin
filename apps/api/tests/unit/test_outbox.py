import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from ruletwin.worker.outbox import CLAIM_SQL, claim_one


async def test_claim_one_uses_skip_locked_and_maps_event() -> None:
    event_id = uuid.uuid4()
    row = {
        "id": event_id,
        "tenant_id": uuid.uuid4(),
        "event_type": "simulation.requested",
        "aggregate_type": "simulation",
        "aggregate_id": uuid.uuid4(),
        "payload": {"simulation_id": str(uuid.uuid4())},
        "attempts": 1,
        "leased_until": datetime.now(UTC),
    }
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    session = AsyncMock()
    session.execute.return_value = result

    claimed = await claim_one(session, lease_owner="worker-1", lease_seconds=30)

    assert "FOR UPDATE SKIP LOCKED" in str(CLAIM_SQL)
    assert claimed is not None
    assert claimed.id == event_id
    session.execute.assert_awaited_once()


async def test_claim_one_returns_none_when_queue_is_empty() -> None:
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = None
    session = AsyncMock()
    session.execute.return_value = result
    assert await claim_one(session, lease_owner="worker-1", lease_seconds=30) is None
