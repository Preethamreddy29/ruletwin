import uuid
from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from ruletwin.api.auth import Identity, authenticated_identity, issue_token, require_roles
from ruletwin.api.problems import ProblemError
from ruletwin.application.vertical_slice import (
    create_approval,
    create_dataset,
    create_rule_version,
    create_simulation,
    evaluate_gate,
    export_evidence,
    get_impact,
    get_simulation,
)
from ruletwin.config import Settings
from ruletwin.db.database import Database
from ruletwin.domain.canonical import JsonValue
from ruletwin.domain.datasets import EVENT_SCHEMA_VERSION, GENERATOR_VERSION
from ruletwin.domain.simulation import ENGINE_VERSION
from ruletwin.scenario import IDENTITIES, TENANTS, identity_by_key

router = APIRouter(prefix="/v1")
AUTH_SCHEME = "bearer"
IdempotencyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)]
Authenticated = Annotated[Identity, Depends(authenticated_identity)]
Author = Annotated[Identity, Depends(require_roles("author"))]
AuthorOrReviewer = Annotated[Identity, Depends(require_roles("author", "reviewer"))]
EvidenceReader = Annotated[
    Identity, Depends(require_roles("author", "reviewer", "release_approver", "auditor"))
]
Reviewer = Annotated[Identity, Depends(require_roles("reviewer"))]
ReleaseApprover = Annotated[Identity, Depends(require_roles("release_approver"))]
AuditReader = Annotated[Identity, Depends(require_roles("reviewer", "release_approver", "auditor"))]
EvidenceExporter = Annotated[
    Identity, Depends(require_roles("reviewer", "release_approver", "auditor"))
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DevTokenRequest(StrictModel):
    identity_key: str = Field(min_length=1, max_length=80)


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


def _development_only(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    if settings.environment not in {"dev", "test"}:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    return settings


def _session(identity: Identity) -> dict[str, object]:
    return {
        "user": {
            "id": identity.actor_id,
            "email": identity.email,
            "display_name": identity.display_name,
        },
        "tenant": {
            "id": identity.tenant_id,
            "slug": identity.tenant_slug,
            "display_name": identity.tenant_display_name,
        },
        "roles": sorted(identity.roles),
        "synthetic": True,
    }


@router.get("/dev/identities", tags=["development"], include_in_schema=False)
async def development_identities(request: Request) -> dict[str, object]:
    _development_only(request)
    tenants = {tenant.id: tenant for tenant in TENANTS}
    return {
        "items": [
            {
                "key": identity.key,
                "display_name": identity.display_name,
                "tenant_id": identity.tenant_id,
                "tenant": tenants[identity.tenant_id].display_name,
                "role": identity.role,
            }
            for identity in IDENTITIES
        ]
    }


@router.post("/dev/token", tags=["development"], include_in_schema=False)
async def development_token(body: DevTokenRequest, request: Request) -> dict[str, object]:
    settings = _development_only(request)
    identity = identity_by_key(body.identity_key)
    if identity is None:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    return {
        "access_token": issue_token(settings, identity.id, identity.tenant_id),
        "token_type": AUTH_SCHEME,
        "expires_in": settings.jwt_ttl_seconds,
    }


@router.get("/dev/session", tags=["development"], include_in_schema=False)
async def development_session(request: Request, identity: Authenticated) -> dict[str, object]:
    _development_only(request)
    return _session(identity)


@router.get("/dev/scenarios", tags=["development"], include_in_schema=False)
async def scenarios(request: Request) -> dict[str, object]:
    _development_only(request)
    return {
        "items": [
            {
                "tenant_id": tenant.id,
                "tenant_slug": tenant.slug,
                "tenant_display_name": tenant.display_name,
                "rule_definition_id": tenant.rule_definition_id,
                "baseline_rule_version_id": tenant.baseline_rule_version_id,
                "dataset_manifest_id": tenant.dataset_id,
                "risk_policy_version_id": tenant.policy_id,
                "engine_version": ENGINE_VERSION,
                "generator_version": GENERATOR_VERSION,
                "event_schema_version": EVENT_SCHEMA_VERSION,
                "seed": 314159 if index == 0 else 271828,
                "event_count": 100,
            }
            for index, tenant in enumerate(TENANTS)
        ]
    }


@router.post("/tenants/{tenant_id}/rule-versions", status_code=status.HTTP_201_CREATED)
async def post_rule_version(
    tenant_id: uuid.UUID,
    body: CreateRule,
    request: Request,
    response: Response,
    identity: Author,
    _idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    if tenant_id != identity.tenant_id:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    if body.effective_until is not None:
        raise ProblemError(422, "Invalid rule", "Open-ended rules are required.", "invalid-rule")
    async with _database(request).session() as session, session.begin():
        result = await create_rule_version(
            session,
            tenant_id=identity.tenant_id,
            actor_id=identity.actor_id,
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
    identity: AuthorOrReviewer,
    _idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    if body.tenant_id != identity.tenant_id:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    async with _database(request).session() as session, session.begin():
        return await create_dataset(
            session,
            tenant_id=identity.tenant_id,
            actor_id=identity.actor_id,
            seed=body.seed,
            event_count=body.event_count,
            correlation_id=_correlation(request),
        )


@router.post("/simulations", status_code=status.HTTP_202_ACCEPTED)
async def post_simulation(
    body: CreateSimulation,
    request: Request,
    response: Response,
    identity: AuthorOrReviewer,
    idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    if body.tenant_id != identity.tenant_id:
        raise ProblemError(404, "Not found", "Resource not found.", "not-found")
    async with _database(request).session() as session, session.begin():
        result, _ = await create_simulation(
            session,
            tenant_id=identity.tenant_id,
            actor_id=identity.actor_id,
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
    simulation_id: uuid.UUID, request: Request, response: Response, identity: EvidenceReader
) -> dict[str, Any]:
    async with _database(request).session() as session:
        result = await get_simulation(session, simulation_id, identity.tenant_id)
    response.headers["ETag"] = f'"{result["version"]}"'
    return result


@router.get("/simulations/{simulation_id}/impact")
async def read_impact(
    simulation_id: uuid.UUID, request: Request, identity: EvidenceReader
) -> dict[str, Any]:
    async with _database(request).session() as session:
        return await get_impact(session, simulation_id, identity.tenant_id)


@router.get("/simulations/{simulation_id}/evidence-export")
async def read_evidence_export(
    simulation_id: uuid.UUID,
    request: Request,
    response: Response,
    identity: EvidenceExporter,
) -> dict[str, Any]:
    async with _database(request).session() as session, session.begin():
        result = await export_evidence(
            session,
            simulation_id=simulation_id,
            tenant_id=identity.tenant_id,
            actor_id=identity.actor_id,
            correlation_id=_correlation(request),
        )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="ruletwin-evidence-{simulation_id}.json"'
    )
    response.headers["ETag"] = f'"{result["export_checksum"]}"'
    return result


@router.post("/simulations/{simulation_id}/approvals", status_code=status.HTTP_201_CREATED)
async def post_approval(
    simulation_id: uuid.UUID,
    body: CreateApproval,
    request: Request,
    identity: Reviewer,
    idempotency_key: IdempotencyHeader,
    if_match: Annotated[str, Header(alias="If-Match")],
) -> dict[str, Any]:
    try:
        expected_version = int(if_match.strip('"'))
    except ValueError as exc:
        raise ProblemError(
            409, "Stale evidence", "If-Match must be the current version ETag.", "stale-evidence"
        ) from exc
    async with _database(request).session() as session, session.begin():
        return await create_approval(
            session,
            simulation_id=simulation_id,
            tenant_id=identity.tenant_id,
            reviewer_id=identity.actor_id,
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
    identity: ReleaseApprover,
    _idempotency_key: IdempotencyHeader,
) -> dict[str, Any]:
    async with _database(request).session() as session, session.begin():
        return await evaluate_gate(
            session,
            tenant_id=identity.tenant_id,
            actor_id=identity.actor_id,
            simulation_id=body.simulation_id,
            approval_id=body.approval_id,
            result_checksum=body.result_checksum,
            policy_id=body.policy_version_id,
            correlation_id=_correlation(request),
        )


@router.get("/audit-events")
async def read_audit_events(
    request: Request, identity: AuditReader, limit: int = 50
) -> dict[str, object]:
    if not 1 <= limit <= 200:
        raise ProblemError(
            422, "Validation failed", "limit must be from 1 through 200.", "validation-failed"
        )
    async with _database(request).session() as session:
        rows = (
            (
                await session.execute(
                    text("""
                        SELECT * FROM audit_events WHERE tenant_id=:tenant_id
                        ORDER BY created_at DESC, id DESC LIMIT :limit
                    """),
                    {"tenant_id": identity.tenant_id, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
    return {"items": [dict(row) for row in rows], "next_cursor": None}
