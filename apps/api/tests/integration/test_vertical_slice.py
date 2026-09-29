import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from ruletwin.api.problems import ProblemError
from ruletwin.application.vertical_slice import (
    create_approval,
    create_rule_version,
    create_simulation,
    evaluate_gate,
    process_simulation_event,
)
from ruletwin.db.database import Database
from ruletwin.scenario import (
    APPROVER_ID,
    AUTHOR_ID,
    BASELINE_RULE_VERSION_ID,
    DATASET_ID,
    POLICY_ID,
    RULE_DEFINITION_ID,
    TENANT_ID,
)
from ruletwin.seed import seed
from ruletwin.worker.outbox import claim_one


@pytest.mark.integration
async def test_vertical_slice_is_idempotent_recoverable_and_checksum_bound() -> None:
    url = os.environ.get("RULETWIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("RULETWIN_TEST_DATABASE_URL is not configured")
    await seed("ruletwin-dev-v1")
    database = Database(url)
    correlation_id = uuid.uuid4()
    idempotency_key = f"integration-{uuid.uuid4()}"
    try:
        async with database.session() as session, session.begin():
            candidate = await create_rule_version(
                session,
                tenant_id=TENANT_ID,
                actor_id=AUTHOR_ID,
                definition_id=RULE_DEFINITION_ID,
                effective_from=datetime.now(UTC).date(),
                timezone="UTC",
                rule={"mode": "half_up", "increment_minor_units": 10},
                correlation_id=correlation_id,
            )
            requested, created = await create_simulation(
                session,
                tenant_id=TENANT_ID,
                actor_id=AUTHOR_ID,
                baseline_id=BASELINE_RULE_VERSION_ID,
                candidate_id=candidate["id"],
                dataset_id=DATASET_ID,
                policy_id=POLICY_ID,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )
            duplicate, duplicate_created = await create_simulation(
                session,
                tenant_id=TENANT_ID,
                actor_id=AUTHOR_ID,
                baseline_id=BASELINE_RULE_VERSION_ID,
                candidate_id=candidate["id"],
                dataset_id=DATASET_ID,
                policy_id=POLICY_ID,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )
            assert created is True
            assert duplicate_created is False
            assert duplicate["id"] == requested["id"]

        async with database.session() as session, session.begin():
            with pytest.raises(ProblemError, match="Evidence incomplete"):
                await create_approval(
                    session,
                    simulation_id=requested["id"],
                    tenant_id=TENANT_ID,
                    reviewer_id=APPROVER_ID,
                    result_checksum="sha256:" + "0" * 64,
                    policy_id=POLICY_ID,
                    decision="approve",
                    rationale=None,
                    idempotency_key=f"incomplete-{uuid.uuid4()}",
                    expected_version=requested["version"],
                    correlation_id=correlation_id,
                )

        # A crash after claim leaves the acknowledged job pending and reclaimable
        # after lease expiry.
        async with database.session() as session, session.begin():
            first_claim = await claim_one(session, lease_owner="crashed-worker", lease_seconds=30)
        assert first_claim is not None
        async with database.session() as session, session.begin():
            await session.execute(
                text("UPDATE outbox_events SET leased_until=:expired WHERE id=:id"),
                {"expired": datetime.now(UTC) - timedelta(seconds=1), "id": first_claim.id},
            )
        async with database.session() as session, session.begin():
            recovered_claim = await claim_one(
                session, lease_owner="recovery-worker", lease_seconds=30
            )
        assert recovered_claim is not None
        assert recovered_claim.id == first_claim.id
        assert recovered_claim.attempts == first_claim.attempts + 1

        async with database.session() as session, session.begin():
            assert (
                await process_simulation_event(
                    session, recovered_claim, worker_id="recovery-worker"
                )
                == "completed"
            )
        async with database.session() as session:
            completed = (
                (
                    await session.execute(
                        text("SELECT * FROM simulations WHERE id=:id"), {"id": requested["id"]}
                    )
                )
                .mappings()
                .one()
            )
            assert completed["status"] == "completed"
            assert completed["result_checksum"].startswith("sha256:")
            impact_count = await session.scalar(
                text("SELECT count(*) FROM impact_deltas WHERE simulation_id=:id"),
                {"id": requested["id"]},
            )
            assert impact_count == 1

        # Simulate a crash after result commit but before message acknowledgement.
        async with database.session() as session, session.begin():
            await session.execute(
                text(
                    """
                    UPDATE outbox_events SET status='pending', processed_at=NULL,
                        leased_until=now() - interval '1 second'
                    WHERE id=:id
                    """
                ),
                {"id": recovered_claim.id},
            )
        async with database.session() as session, session.begin():
            replay = await claim_one(session, lease_owner="replay-worker", lease_seconds=30)
        assert replay is not None
        async with database.session() as session, session.begin():
            assert (
                await process_simulation_event(session, replay, worker_id="replay-worker")
                == "already-completed"
            )
        async with database.session() as session:
            assert (
                await session.scalar(
                    text("SELECT count(*) FROM impact_deltas WHERE simulation_id=:id"),
                    {"id": requested["id"]},
                )
                == 1
            )

        async with database.session() as session, session.begin():
            with pytest.raises(ProblemError, match="Separation of duties"):
                await create_approval(
                    session,
                    simulation_id=requested["id"],
                    tenant_id=TENANT_ID,
                    reviewer_id=AUTHOR_ID,
                    result_checksum=completed["result_checksum"],
                    policy_id=POLICY_ID,
                    decision="approve",
                    rationale=None,
                    idempotency_key=f"self-{uuid.uuid4()}",
                    expected_version=completed["version"],
                    correlation_id=correlation_id,
                )
            with pytest.raises(ProblemError, match="Stale evidence"):
                await create_approval(
                    session,
                    simulation_id=requested["id"],
                    tenant_id=TENANT_ID,
                    reviewer_id=APPROVER_ID,
                    result_checksum="sha256:" + "0" * 64,
                    policy_id=POLICY_ID,
                    decision="approve",
                    rationale=None,
                    idempotency_key=f"stale-{uuid.uuid4()}",
                    expected_version=completed["version"],
                    correlation_id=correlation_id,
                )
            approval = await create_approval(
                session,
                simulation_id=requested["id"],
                tenant_id=TENANT_ID,
                reviewer_id=APPROVER_ID,
                result_checksum=completed["result_checksum"],
                policy_id=POLICY_ID,
                decision="approve",
                rationale="Integration evidence reviewed.",
                idempotency_key=f"approval-{uuid.uuid4()}",
                expected_version=completed["version"],
                correlation_id=correlation_id,
            )
            gate = await evaluate_gate(
                session,
                tenant_id=TENANT_ID,
                actor_id=APPROVER_ID,
                simulation_id=requested["id"],
                approval_id=approval["id"],
                result_checksum=completed["result_checksum"],
                policy_id=POLICY_ID,
                correlation_id=correlation_id,
            )
            assert gate["decision"] == "block"
            audit_actions = set(
                (
                    await session.execute(
                        text(
                            """
                            SELECT action FROM audit_events
                            WHERE tenant_id=:tenant_id AND correlation_id=:correlation_id
                            """
                        ),
                        {"tenant_id": TENANT_ID, "correlation_id": correlation_id},
                    )
                ).scalars()
            )
            assert {
                "rule_version.created",
                "simulation.requested",
                "simulation.queued",
                "simulation.running",
                "simulation.completed",
                "approval.created",
                "release_gate.evaluated",
            } <= audit_actions
    finally:
        await database.dispose()
