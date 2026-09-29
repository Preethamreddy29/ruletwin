import uuid
from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Header, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from ruletwin.api.problems import ProblemError
from ruletwin.application.vertical_slice import (
    create_approval,
    create_dataset,
    create_rule_version,
    create_simulation,
    evaluate_gate,
    get_impact,
    get_simulation,
)
from ruletwin.db.database import Database
from ruletwin.domain.canonical import JsonValue
from ruletwin.domain.datasets import EVENT_SCHEMA_VERSION, GENERATOR_VERSION
from ruletwin.domain.simulation import ENGINE_VERSION
from ruletwin.scenario import (
    APPROVER_ID,
    AUTHOR_ID,
    BASELINE_RULE_VERSION_ID,
    DATASET_ID,
    POLICY_ID,
    RULE_DEFINITION_ID,
    TENANT_ID,
)

router = APIRouter(prefix="/v1")
ActorHeader = Annotated[uuid.UUID, Header(alias="X-Actor-ID")]
IdempotencyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRule(StrictModel):
    definition_id: uuid.UUID
    family: Literal["rounding"]
    effective_from: date
    effective_until: date | None = None
    timezone: str
    rule: dict[str, JsonValue]
    dependency_version_ids: list[uuid.UUID] = Field(default_factory=list, max_length=0)


class CreateDataset(StrictModel):
    tenant_id: uuid.UUID
    seed: int = Field(ge=0)
    generator_version: Literal["rounding-events-v1"]
    event_schema_version: Literal["business-event-v1"]
    event_count: int = Field(ge=1, le=100000)


class CreateSimulation(StrictModel):
    tenant_id: uuid.UUID
    baseline_rule_version_id: uuid.UUID
    candidate_rule_version_id: uuid.UUID
    dataset_manifest_id: uuid.UUID
    engine_version: Literal["rounding-engine-v1"]
    risk_policy_version_id: uuid.UUID


class CreateApproval(StrictModel):
    result_checksum: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    policy_version_id: uuid.UUID
    decision: Literal["approve", "reject"]
    rationale: str | None = Field(default=None, max_length=2000)


class EvaluateGate(StrictModel):
    simulation_id: uuid.UUID
    approval_id: uuid.UUID
    result_checksum: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    policy_version_id: uuid.UUID


def _database(request: Request) -> Database:
    return request.app.state.database  # type: ignore[no-any-return]


def _correlation(request: Request) -> uuid.UUID:
    return uuid.UUID(request.state.request_id)


async def _require_role(session: Any, actor_id: uuid.UUID, tenant_id: uuid.UUID, role: str) -> None:
    allowed = await session.scalar(
        text(
            """
            SELECT 1 FROM user_tenant_roles
            WHERE user_id=:actor_id AND tenant_id=:tenant_id AND role_code=:role
            """
        ),
        {"actor_id": actor_id, "tenant_id": tenant_id, "role": role},
    )
    if allowed is None:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")


@router.get("/dev/scenario", tags=["development"], include_in_schema=False)
async def scenario() -> dict[str, object]:
    return {
        "tenant_id": TENANT_ID,
        "author_id": AUTHOR_ID,
        "approver_id": APPROVER_ID,
        "rule_definition_id": RULE_DEFINITION_ID,
        "baseline_rule_version_id": BASELINE_RULE_VERSION_ID,
        "dataset_manifest_id": DATASET_ID,
        "risk_policy_version_id": POLICY_ID,
        "engine_version": ENGINE_VERSION,
        "generator_version": GENERATOR_VERSION,
        "event_schema_version": EVENT_SCHEMA_VERSION,
    }


@router.post("/tenants/{tenant_id}/rule-versions", status_code=status.HTTP_201_CREATED)
async def post_rule_version(
    tenant_id: uuid.UUID,
    body: CreateRule,
    request: Request,
    response: Response,
    actor_id: ActorHeader,
    _idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    if tenant_id != TENANT_ID or body.effective_until is not None:
        raise ProblemError(
            422,
            "Invalid rule",
            "Phase 3 accepts the fixed tenant and open-ended rule only.",
            "invalid-rule",
        )
    database = _database(request)
    async with database.session() as session, session.begin():
        await _require_role(session, actor_id, tenant_id, "author")
        result = await create_rule_version(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            definition_id=body.definition_id,
            effective_from=body.effective_from,
            timezone=body.timezone,
            rule=body.rule,
            correlation_id=_correlation(request),
        )
    response.headers["ETag"] = f'"{result["checksum"]}"'
    return result


@router.post("/replay-datasets", status_code=status.HTTP_201_CREATED)
async def post_dataset(
    body: CreateDataset,
    request: Request,
    actor_id: ActorHeader,
    _idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    if body.tenant_id != TENANT_ID:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    database = _database(request)
    async with database.session() as session, session.begin():
        await _require_role(session, actor_id, body.tenant_id, "author")
        return await create_dataset(
            session,
            tenant_id=body.tenant_id,
            actor_id=actor_id,
            seed=body.seed,
            event_count=body.event_count,
            correlation_id=_correlation(request),
        )


@router.post("/simulations", status_code=status.HTTP_202_ACCEPTED)
async def post_simulation(
    body: CreateSimulation,
    request: Request,
    response: Response,
    actor_id: ActorHeader,
    idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    if body.tenant_id != TENANT_ID:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    database = _database(request)
    async with database.session() as session, session.begin():
        await _require_role(session, actor_id, body.tenant_id, "author")
        result, _ = await create_simulation(
            session,
            tenant_id=body.tenant_id,
            actor_id=actor_id,
            baseline_id=body.baseline_rule_version_id,
            candidate_id=body.candidate_rule_version_id,
            dataset_id=body.dataset_manifest_id,
            policy_id=body.risk_policy_version_id,
            idempotency_key=idempotency_key,
            correlation_id=_correlation(request),
        )
    response.headers["Location"] = f"/v1/simulations/{result['id']}"
    response.headers["ETag"] = f'"{result["version"]}"'
    return result


@router.get("/simulations/{simulation_id}")
async def read_simulation(
    simulation_id: uuid.UUID, request: Request, response: Response
) -> dict[str, Any]:
    database = _database(request)
    async with database.session() as session:
        result = await get_simulation(session, simulation_id, TENANT_ID)
    response.headers["ETag"] = f'"{result["version"]}"'
    return result


@router.get("/simulations/{simulation_id}/impact")
async def read_impact(simulation_id: uuid.UUID, request: Request) -> dict[str, Any]:
    database = _database(request)
    async with database.session() as session:
        return await get_impact(session, simulation_id, TENANT_ID)


@router.post("/simulations/{simulation_id}/approvals", status_code=status.HTTP_201_CREATED)
async def post_approval(
    simulation_id: uuid.UUID,
    body: CreateApproval,
    request: Request,
    actor_id: ActorHeader,
    idempotency_key: IdempotencyHeader,
    if_match: Annotated[str, Header(alias="If-Match")],
) -> dict[str, Any]:
    try:
        expected_version = int(if_match.strip('"'))
    except ValueError as exc:
        raise ProblemError(
            409, "Stale evidence", "If-Match must be the current version ETag.", "stale-evidence"
        ) from exc
    database = _database(request)
    async with database.session() as session, session.begin():
        await _require_role(session, actor_id, TENANT_ID, "reviewer")
        return await create_approval(
            session,
            simulation_id=simulation_id,
            tenant_id=TENANT_ID,
            reviewer_id=actor_id,
            result_checksum=body.result_checksum,
            policy_id=body.policy_version_id,
            decision=body.decision,
            rationale=body.rationale,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            correlation_id=_correlation(request),
        )


@router.post("/release-gates/evaluate", status_code=status.HTTP_201_CREATED)
async def post_gate(
    body: EvaluateGate,
    request: Request,
    actor_id: ActorHeader,
    _idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    database = _database(request)
    async with database.session() as session, session.begin():
        await _require_role(session, actor_id, TENANT_ID, "release_approver")
        return await evaluate_gate(
            session,
            tenant_id=TENANT_ID,
            actor_id=actor_id,
            simulation_id=body.simulation_id,
            approval_id=body.approval_id,
            result_checksum=body.result_checksum,
            policy_id=body.policy_version_id,
            correlation_id=_correlation(request),
        )


@router.get("/audit-events")
async def read_audit_events(request: Request, limit: int = 50) -> dict[str, object]:
    if not 1 <= limit <= 200:
        raise ProblemError(
            422, "Validation failed", "limit must be from 1 through 200.", "validation-failed"
        )
    database = _database(request)
    async with database.session() as session:
        rows = (
            (
                await session.execute(
                    text(
                        """
                    SELECT * FROM audit_events WHERE tenant_id=:tenant_id
                    ORDER BY created_at DESC, id DESC LIMIT :limit
                    """
                    ),
                    {"tenant_id": TENANT_ID, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
    return {"items": [dict(row) for row in rows], "next_cursor": None}
