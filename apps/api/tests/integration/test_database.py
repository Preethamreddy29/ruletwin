import os
import uuid

import pytest
from sqlalchemy import text

from ruletwin.db.database import Database
from ruletwin.worker.outbox import claim_one


@pytest.mark.integration
async def test_database_readiness_and_safe_outbox_claim() -> None:
    url = os.environ.get("RULETWIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("RULETWIN_TEST_DATABASE_URL is not configured")
    database = Database(url)
    tenant_id = uuid.uuid4()
    event_id = uuid.uuid4()
    try:
        assert await database.ping() is True
        async with database.session() as session, session.begin():
            await session.execute(
                text("INSERT INTO tenants (id, slug, display_name) VALUES (:id, :slug, 'Test')"),
                {"id": tenant_id, "slug": f"test-{tenant_id}"},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO outbox_events
                        (id, tenant_id, event_type, aggregate_type, aggregate_id, payload)
                    VALUES
                        (:id, :tenant_id, 'test.requested', 'test', :aggregate_id, '{}'::jsonb)
                    """
                ),
                {"id": event_id, "tenant_id": tenant_id, "aggregate_id": uuid.uuid4()},
            )
        async with database.session() as session, session.begin():
            claimed = await claim_one(session, lease_owner="integration-test", lease_seconds=30)
        assert claimed is not None
        assert claimed.id == event_id
        assert claimed.attempts == 1
    finally:
        async with database.session() as session, session.begin():
            await session.execute(
                text("DELETE FROM outbox_events WHERE id = :id"), {"id": event_id}
            )
            await session.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tenant_id})
        await database.dispose()
