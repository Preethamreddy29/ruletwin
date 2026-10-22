import json
import uuid
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ruletwin.api.problems import ProblemError
from ruletwin.domain.canonical import JsonValue, canonical_json, checksum, normalize_json
from ruletwin.domain.datasets import (
    EVENT_SCHEMA_VERSION,
    GENERATOR_VERSION,
    dataset_checksum,
    generate_events,
)
from ruletwin.domain.rounding import RoundingRule
from ruletwin.domain.simulation import ENGINE_VERSION, compare_rules, evaluate_risk
from ruletwin.worker.outbox import ClaimedEvent


def _json(value: object) -> str:
    return canonical_json(normalize_json(value))


async def append_audit(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    correlation_id: uuid.UUID,
    metadata: dict[str, JsonValue] | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO audit_events
                (id, tenant_id, actor_id, action, object_type, object_id,
                 result, correlation_id, metadata)
            VALUES (:id, :tenant_id, :actor_id, :action, :object_type, :object_id,
                    'success', :correlation_id, CAST(:metadata AS jsonb))
            """
        ),
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "action": action,
            "object_type": object_type,
            "object_id": object_id,
            "correlation_id": correlation_id,
            "metadata": _json(metadata or {}),
        },
    )


async def create_rule_version(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    definition_id: uuid.UUID,
    effective_from: date,
    timezone: str,
    rule: dict[str, JsonValue],
    correlation_id: uuid.UUID,
) -> dict[str, Any]:
    RoundingRule.from_json(rule)
    if timezone != "UTC":
        raise ProblemError(
            422, "Invalid rule", "Phase 3 requires the UTC timezone.", "invalid-rule"
        )
    rule_checksum = checksum(rule)
    existing = (
        (
            await session.execute(
                text(
                    """
                SELECT * FROM rule_versions
                WHERE tenant_id = :tenant_id AND checksum = :checksum
                """
                ),
                {"tenant_id": tenant_id, "checksum": rule_checksum},
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        return dict(existing)
    definition_exists = await session.scalar(
        text("SELECT 1 FROM rule_definitions WHERE id=:id AND tenant_id=:tenant_id"),
        {"id": definition_id, "tenant_id": tenant_id},
    )
    if definition_exists is None:
        raise ProblemError(422, "Invalid rule", "Rule definition is not available.", "invalid-rule")
    version_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO rule_versions
                (id, tenant_id, definition_id, family, effective_from, timezone,
                 schema_version, rule, canonical_rule, checksum, authored_by)
            VALUES (:id, :tenant_id, :definition_id, 'rounding', :effective_from, :timezone,
                    'rounding-rule-v1', CAST(:rule AS jsonb), :canonical_rule, :checksum, :actor_id)
            """
        ),
        {
            "id": version_id,
            "tenant_id": tenant_id,
            "definition_id": definition_id,
            "effective_from": effective_from,
            "timezone": timezone,
            "rule": canonical_json(rule),
            "canonical_rule": canonical_json(rule),
            "checksum": rule_checksum,
            "actor_id": actor_id,
        },
    )
    await append_audit(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="rule_version.created",
        object_type="rule_version",
        object_id=version_id,
        correlation_id=correlation_id,
        metadata={"checksum": rule_checksum},
    )
    row = (
        (
            await session.execute(
                text("SELECT * FROM rule_versions WHERE id=:id"), {"id": version_id}
            )
        )
        .mappings()
        .one()
    )
    return dict(row)


async def create_dataset(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    seed: int,
    event_count: int,
    correlation_id: uuid.UUID,
) -> dict[str, Any]:
    events = generate_events(seed, event_count)
    manifest_checksum = dataset_checksum(seed, events)
    existing = (
        (
            await session.execute(
                text(
                    """
                    SELECT * FROM dataset_manifests
                    WHERE tenant_id=:tenant_id AND checksum=:checksum
                    """
                ),
                {"tenant_id": tenant_id, "checksum": manifest_checksum},
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        return dict(existing)
    manifest_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO dataset_manifests
                (id, tenant_id, seed, generator_version, event_schema_version,
                 event_count, checksum, created_by)
            VALUES (:id, :tenant_id, :seed, :generator_version, :schema_version,
                    :event_count, :checksum, :actor_id)
            """
        ),
        {
            "id": manifest_id,
            "tenant_id": tenant_id,
            "seed": seed,
            "generator_version": GENERATOR_VERSION,
            "schema_version": EVENT_SCHEMA_VERSION,
            "event_count": event_count,
            "checksum": manifest_checksum,
            "actor_id": actor_id,
        },
    )
    for event in events:
        event_row_id = uuid.uuid5(
            uuid.UUID("85d6a1fd-73a7-5d58-9413-1b80931ad0b3"),
            f"{manifest_checksum}:{event['sequence']}",
        )
        await session.execute(
            text(
                """
                INSERT INTO business_events
                    (id, tenant_id, dataset_manifest_id, sequence, payload, checksum)
                VALUES (:id, :tenant_id, :manifest_id, :sequence,
                        CAST(:payload AS jsonb), :checksum)
                """
            ),
            {
                "id": event_row_id,
                "tenant_id": tenant_id,
                "manifest_id": manifest_id,
                "sequence": event["sequence"],
                "payload": canonical_json(event),
                "checksum": checksum(event),
            },
        )
    await append_audit(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="dataset.created",
        object_type="dataset_manifest",
        object_id=manifest_id,
        correlation_id=correlation_id,
        metadata={"checksum": manifest_checksum, "event_count": event_count},
    )
    row = (
        (
            await session.execute(
                text("SELECT * FROM dataset_manifests WHERE id=:id"), {"id": manifest_id}
            )
        )
        .mappings()
        .one()
    )
    return dict(row)


async def create_simulation(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    baseline_id: uuid.UUID,
    candidate_id: uuid.UUID,
    dataset_id: uuid.UUID,
    policy_id: uuid.UUID,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> tuple[dict[str, Any], bool]:
    existing = (
        (
            await session.execute(
                text(
                    """
                SELECT * FROM simulations
                WHERE tenant_id=:tenant_id AND requested_by=:actor_id
                  AND idempotency_key=:idempotency_key
                """
                ),
                {
                    "tenant_id": tenant_id,
                    "actor_id": actor_id,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        expected = (baseline_id, candidate_id, dataset_id, policy_id)
        actual = tuple(
            existing[key]
            for key in (
                "baseline_rule_version_id",
                "candidate_rule_version_id",
                "dataset_manifest_id",
                "risk_policy_version_id",
            )
        )
        if expected != actual:
            raise ProblemError(
                409,
                "Idempotency conflict",
                "The idempotency key was already used for a different request.",
                "idempotency-conflict",
            )
        return dict(existing), False
    valid = await session.scalar(
        text(
            """
            SELECT 1
            FROM rule_versions baseline
            JOIN rule_versions candidate ON candidate.id=:candidate_id
            JOIN dataset_manifests dataset ON dataset.id=:dataset_id
            JOIN risk_policies policy ON policy.id=:policy_id
            WHERE baseline.id=:baseline_id
              AND baseline.tenant_id=:tenant_id AND candidate.tenant_id=:tenant_id
              AND dataset.tenant_id=:tenant_id AND policy.tenant_id=:tenant_id
              AND baseline.family='rounding' AND candidate.family='rounding'
            """
        ),
        {
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
            "dataset_id": dataset_id,
            "policy_id": policy_id,
            "tenant_id": tenant_id,
        },
    )
    if valid is None:
        raise ProblemError(
            422, "Invalid simulation", "The immutable version tuple is invalid.", "invalid-tuple"
        )
    simulation_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO simulations
                (id, tenant_id, baseline_rule_version_id, candidate_rule_version_id,
                 dataset_manifest_id, engine_version, risk_policy_version_id,
                 status, requested_by, idempotency_key)
            VALUES (:id, :tenant_id, :baseline_id, :candidate_id, :dataset_id,
                    :engine_version, :policy_id, 'requested', :actor_id, :idempotency_key)
            """
        ),
        {
            "id": simulation_id,
            "tenant_id": tenant_id,
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
            "dataset_id": dataset_id,
            "engine_version": ENGINE_VERSION,
            "policy_id": policy_id,
            "actor_id": actor_id,
            "idempotency_key": idempotency_key,
        },
    )
    await append_audit(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="simulation.requested",
        object_type="simulation",
        object_id=simulation_id,
        correlation_id=correlation_id,
    )
    await session.execute(
        text("UPDATE simulations SET status='queued', version=version+1 WHERE id=:id"),
        {"id": simulation_id},
    )
    await append_audit(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="simulation.queued",
        object_type="simulation",
        object_id=simulation_id,
        correlation_id=correlation_id,
    )
    await session.execute(
        text(
            """
            INSERT INTO outbox_events
                (id, tenant_id, event_type, aggregate_type, aggregate_id, payload)
            VALUES (:id, :tenant_id, 'simulation.requested', 'simulation',
                    :simulation_id, CAST(:payload AS jsonb))
            """
        ),
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "simulation_id": simulation_id,
            "payload": _json(
                {"simulation_id": str(simulation_id), "correlation_id": str(correlation_id)}
            ),
        },
    )
    row = (
        (
            await session.execute(
                text("SELECT * FROM simulations WHERE id=:id"), {"id": simulation_id}
            )
        )
        .mappings()
        .one()
    )
    return dict(row), True


async def process_simulation_event(
    session: AsyncSession, event: ClaimedEvent, *, worker_id: str
) -> str:
    if event.event_type != "simulation.requested":
        await session.execute(
            text(
                """
                UPDATE outbox_events SET status='failed', last_error='unsupported event'
                WHERE id=:id
                """
            ),
            {"id": event.id},
        )
        return "failed"
    simulation = (
        (
            await session.execute(
                text("SELECT * FROM simulations WHERE id=:id AND tenant_id=:tenant_id FOR UPDATE"),
                {"id": event.aggregate_id, "tenant_id": event.tenant_id},
            )
        )
        .mappings()
        .one()
    )
    if simulation["status"] == "completed":
        await session.execute(
            text("UPDATE outbox_events SET status='processed', processed_at=now() WHERE id=:id"),
            {"id": event.id},
        )
        return "already-completed"
    correlation_value = event.payload.get("correlation_id", str(event.id))
    correlation_id = uuid.UUID(str(correlation_value))
    run_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO simulation_runs
                (id, tenant_id, simulation_id, attempt, status, worker_id, heartbeat_at)
            VALUES (:id, :tenant_id, :simulation_id, :attempt, 'running', :worker_id, now())
            ON CONFLICT (simulation_id, attempt) DO NOTHING
            """
        ),
        {
            "id": run_id,
            "tenant_id": event.tenant_id,
            "simulation_id": event.aggregate_id,
            "attempt": event.attempts,
            "worker_id": worker_id,
        },
    )
    await session.execute(
        text("UPDATE simulations SET status='running', version=version+1 WHERE id=:id"),
        {"id": event.aggregate_id},
    )
    await append_audit(
        session,
        tenant_id=event.tenant_id,
        actor_id=simulation["requested_by"],
        action="simulation.running",
        object_type="simulation",
        object_id=event.aggregate_id,
        correlation_id=correlation_id,
        metadata={"attempt": event.attempts, "worker_id": worker_id},
    )
    rules = (
        (
            await session.execute(
                text(
                    """
                SELECT baseline.rule AS baseline_rule, candidate.rule AS candidate_rule
                FROM rule_versions baseline, rule_versions candidate
                WHERE baseline.id=:baseline_id AND candidate.id=:candidate_id
                """
                ),
                {
                    "baseline_id": simulation["baseline_rule_version_id"],
                    "candidate_id": simulation["candidate_rule_version_id"],
                },
            )
        )
        .mappings()
        .one()
    )
    event_rows: list[Any] = list(
        (
            await session.execute(
                text(
                    """
                SELECT payload FROM business_events
                WHERE dataset_manifest_id=:dataset_id AND tenant_id=:tenant_id
                ORDER BY sequence
                """
                ),
                {"dataset_id": simulation["dataset_manifest_id"], "tenant_id": event.tenant_id},
            )
        )
        .scalars()
        .all()
    )
    domain_events = [cast(dict[str, JsonValue], row) for row in event_rows]
    result = compare_rules(rules["baseline_rule"], rules["candidate_rule"], domain_events)
    policy = (
        (
            await session.execute(
                text("SELECT * FROM risk_policies WHERE id=:id AND tenant_id=:tenant_id"),
                {"id": simulation["risk_policy_version_id"], "tenant_id": event.tenant_id},
            )
        )
        .mappings()
        .one()
    )
    risk = evaluate_risk(
        result.impact,
        policy["financial_delta_threshold_minor_units"],
        policy["version"],
    )
    for outcome in result.outcomes:
        await session.execute(
            text(
                """
                INSERT INTO outcomes
                    (id, tenant_id, simulation_run_id, event_sequence, baseline,
                     candidate, financial_delta_minor_units)
                VALUES (:id, :tenant_id, :run_id, :sequence, CAST(:baseline AS jsonb),
                        CAST(:candidate AS jsonb), :delta)
                ON CONFLICT (simulation_run_id, event_sequence) DO NOTHING
                """
            ),
            {
                "id": uuid.uuid4(),
                "tenant_id": event.tenant_id,
                "run_id": run_id,
                "sequence": outcome["sequence"],
                "baseline": _json(outcome["baseline"]),
                "candidate": _json(outcome["candidate"]),
                "delta": outcome["financial_delta_minor_units"],
            },
        )
    await session.execute(
        text(
            """
            INSERT INTO impact_deltas (id, tenant_id, simulation_id, summary, checksum)
            VALUES (:id, :tenant_id, :simulation_id, CAST(:summary AS jsonb), :checksum)
            ON CONFLICT (simulation_id) DO NOTHING
            """
        ),
        {
            "id": uuid.uuid4(),
            "tenant_id": event.tenant_id,
            "simulation_id": event.aggregate_id,
            "summary": _json(result.impact),
            "checksum": checksum(result.impact),
        },
    )
    await session.execute(
        text(
            """
            INSERT INTO risk_evaluations
                (id, tenant_id, simulation_id, policy_version_id, decision, reasons, checksum)
            VALUES (:id, :tenant_id, :simulation_id, :policy_id, :decision,
                    CAST(:reasons AS jsonb), :checksum)
            ON CONFLICT (simulation_id) DO NOTHING
            """
        ),
        {
            "id": uuid.uuid4(),
            "tenant_id": event.tenant_id,
            "simulation_id": event.aggregate_id,
            "policy_id": simulation["risk_policy_version_id"],
            "decision": risk["decision"],
            "reasons": _json(risk["reasons"]),
            "checksum": risk["checksum"],
        },
    )
    await session.execute(
        text(
            """
            UPDATE simulation_runs SET status='completed', completed_at=now(),
                heartbeat_at=now(), result_checksum=:checksum
            WHERE simulation_id=:simulation_id AND attempt=:attempt
            """
        ),
        {
            "checksum": result.result_checksum,
            "simulation_id": event.aggregate_id,
            "attempt": event.attempts,
        },
    )
    await session.execute(
        text(
            """
            UPDATE simulations SET status='completed', version=version+1,
                result_checksum=:checksum, completed_at=now()
            WHERE id=:id
            """
        ),
        {"checksum": result.result_checksum, "id": event.aggregate_id},
    )
    await session.execute(
        text("UPDATE outbox_events SET status='processed', processed_at=now() WHERE id=:id"),
        {"id": event.id},
    )
    await append_audit(
        session,
        tenant_id=event.tenant_id,
        actor_id=simulation["requested_by"],
        action="simulation.completed",
        object_type="simulation",
        object_id=event.aggregate_id,
        correlation_id=correlation_id,
        metadata={"result_checksum": result.result_checksum},
    )
    return "completed"


async def get_simulation(
    session: AsyncSession, simulation_id: uuid.UUID, tenant_id: uuid.UUID
) -> dict[str, Any]:
    row = (
        (
            await session.execute(
                text("SELECT * FROM simulations WHERE id=:id AND tenant_id=:tenant_id"),
                {"id": simulation_id, "tenant_id": tenant_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ProblemError(404, "Not found", "Simulation was not found.", "not-found")
    return dict(row)


async def get_impact(
    session: AsyncSession, simulation_id: uuid.UUID, tenant_id: uuid.UUID
) -> dict[str, Any]:
    row = (
        (
            await session.execute(
                text(
                    """
                SELECT s.id AS simulation_id, s.result_checksum, s.status,
                       i.summary, i.checksum AS impact_checksum,
                       r.policy_version_id, r.decision, r.reasons,
                       r.checksum AS risk_checksum
                FROM simulations s
                LEFT JOIN impact_deltas i ON i.simulation_id=s.id
                LEFT JOIN risk_evaluations r ON r.simulation_id=s.id
                WHERE s.id=:id AND s.tenant_id=:tenant_id
                """
                ),
                {"id": simulation_id, "tenant_id": tenant_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ProblemError(404, "Not found", "Simulation was not found.", "not-found")
    if row["status"] != "completed":
        raise ProblemError(
            409, "Evidence incomplete", "Simulation has not completed.", "evidence-incomplete"
        )
    return {
        "simulation_id": row["simulation_id"],
        "result_checksum": row["result_checksum"],
        "impact_checksum": row["impact_checksum"],
        "summary": row["summary"],
        "risk": {
            "policy_version_id": row["policy_version_id"],
            "decision": row["decision"],
            "reasons": row["reasons"],
            "checksum": row["risk_checksum"],
        },
    }


async def create_approval(
    session: AsyncSession,
    *,
    simulation_id: uuid.UUID,
    tenant_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    result_checksum: str,
    policy_id: uuid.UUID,
    decision: str,
    rationale: str | None,
    idempotency_key: str,
    expected_version: int,
    correlation_id: uuid.UUID,
) -> dict[str, Any]:
    simulation = (
        (
            await session.execute(
                text("SELECT * FROM simulations WHERE id=:id AND tenant_id=:tenant_id FOR UPDATE"),
                {"id": simulation_id, "tenant_id": tenant_id},
            )
        )
        .mappings()
        .one_or_none()
    )
    if simulation is None:
        raise ProblemError(404, "Not found", "Simulation was not found.", "not-found")
    if simulation["status"] != "completed":
        raise ProblemError(
            409,
            "Evidence incomplete",
            "Only completed evidence can be approved.",
            "evidence-incomplete",
        )
    if simulation["version"] != expected_version:
        raise ProblemError(
            409, "Stale evidence", "The simulation version has changed.", "stale-evidence"
        )
    if simulation["requested_by"] == reviewer_id:
        raise ProblemError(
            409, "Separation of duties", "The evidence author cannot approve it.", "self-approval"
        )
    if (
        simulation["result_checksum"] != result_checksum
        or simulation["risk_policy_version_id"] != policy_id
    ):
        raise ProblemError(
            409,
            "Stale evidence",
            "The result checksum or policy version is stale.",
            "stale-evidence",
        )
    existing = (
        (
            await session.execute(
                text(
                    """
                SELECT * FROM approvals WHERE simulation_id=:simulation_id
                  AND reviewer_id=:reviewer_id AND idempotency_key=:idempotency_key
                """
                ),
                {
                    "simulation_id": simulation_id,
                    "reviewer_id": reviewer_id,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        return dict(existing)
    approval_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO approvals
                (id, tenant_id, simulation_id, reviewer_id, result_checksum,
                 policy_version_id, decision, rationale, idempotency_key)
            VALUES (:id, :tenant_id, :simulation_id, :reviewer_id, :result_checksum,
                    :policy_id, :decision, :rationale, :idempotency_key)
            """
        ),
        {
            "id": approval_id,
            "tenant_id": tenant_id,
            "simulation_id": simulation_id,
            "reviewer_id": reviewer_id,
            "result_checksum": result_checksum,
            "policy_id": policy_id,
            "decision": decision,
            "rationale": rationale,
            "idempotency_key": idempotency_key,
        },
    )
    await append_audit(
        session,
        tenant_id=tenant_id,
        actor_id=reviewer_id,
        action="approval.created",
        object_type="approval",
        object_id=approval_id,
        correlation_id=correlation_id,
        metadata={"decision": decision, "result_checksum": result_checksum},
    )
    row = (
        (await session.execute(text("SELECT * FROM approvals WHERE id=:id"), {"id": approval_id}))
        .mappings()
        .one()
    )
    return dict(row)


async def evaluate_gate(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    simulation_id: uuid.UUID,
    approval_id: uuid.UUID,
    result_checksum: str,
    policy_id: uuid.UUID,
    correlation_id: uuid.UUID,
) -> dict[str, Any]:
    evidence = (
        (
            await session.execute(
                text(
                    """
                SELECT s.result_checksum, s.status, s.risk_policy_version_id,
                       a.decision AS approval_decision, a.result_checksum AS approval_checksum,
                       a.policy_version_id AS approval_policy_id, r.decision AS risk_decision
                FROM simulations s
                JOIN approvals a ON a.simulation_id=s.id AND a.id=:approval_id
                JOIN risk_evaluations r ON r.simulation_id=s.id
                WHERE s.id=:simulation_id AND s.tenant_id=:tenant_id
                """
                ),
                {
                    "approval_id": approval_id,
                    "simulation_id": simulation_id,
                    "tenant_id": tenant_id,
                },
            )
        )
        .mappings()
        .one_or_none()
    )
    if evidence is None:
        allow = False
    else:
        exact = (
            evidence["status"] == "completed"
            and evidence["result_checksum"] == result_checksum
            and evidence["approval_checksum"] == result_checksum
            and evidence["risk_policy_version_id"] == policy_id
            and evidence["approval_policy_id"] == policy_id
        )
        allow = (
            exact
            and evidence["approval_decision"] == "approve"
            and evidence["risk_decision"] == "allow"
        )
    decision = "allow" if allow else "block"
    reasons = (
        ["Approval and policy allow the exact immutable evidence."]
        if allow
        else ["Evidence is stale, rejected, incomplete, or blocked by policy."]
    )
    gate_evidence = {
        "simulation_id": str(simulation_id),
        "approval_id": str(approval_id),
        "result_checksum": result_checksum,
        "policy_version_id": str(policy_id),
        "decision": decision,
    }
    gate_id = uuid.uuid4()
    await session.execute(
        text(
            """
            INSERT INTO release_gates
                (id, tenant_id, simulation_id, approval_id, decision, evidence_checksum, reasons)
            VALUES (:id, :tenant_id, :simulation_id, :approval_id, :decision,
                    :checksum, CAST(:reasons AS jsonb))
            ON CONFLICT (simulation_id, approval_id) DO NOTHING
            """
        ),
        {
            "id": gate_id,
            "tenant_id": tenant_id,
            "simulation_id": simulation_id,
            "approval_id": approval_id,
            "decision": decision,
            "checksum": checksum(normalize_json(gate_evidence)),
            "reasons": json.dumps(reasons),
        },
    )
    await append_audit(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="release_gate.evaluated",
        object_type="release_gate",
        object_id=gate_id,
        correlation_id=correlation_id,
        metadata={"decision": decision},
    )
    row = (
        (
            await session.execute(
                text(
                    """
                    SELECT * FROM release_gates
                    WHERE simulation_id=:simulation_id AND approval_id=:approval_id
                    """
                ),
                {"simulation_id": simulation_id, "approval_id": approval_id},
            )
        )
        .mappings()
        .one()
    )
    return dict(row)


def utc_now() -> datetime:
    return datetime.now(UTC)
