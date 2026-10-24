import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from ruletwin.api.app import create_app
from ruletwin.api.auth import issue_token
from ruletwin.application.vertical_slice import process_simulation_event
from ruletwin.config import Settings
from ruletwin.db.database import Database
from ruletwin.scenario import (
    APPROVER_ID,
    AUDITOR_ID,
    AUTHOR_ID,
    BASELINE_RULE_VERSION_ID,
    DATASET_ID,
    POLICY_ID,
    REVIEWER_ID,
    RULE_DEFINITION_ID,
    SECOND_AUDITOR_ID,
    SECOND_REVIEWER_ID,
    SECOND_TENANT_ID,
    TENANT_ID,
)
from ruletwin.seed import seed
from ruletwin.worker.outbox import claim_one


def _headers(token: str, *, idempotency: bool = False) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency:
        headers["Idempotency-Key"] = f"authz-{uuid.uuid4()}"
    return headers


@pytest.mark.integration
async def test_multitenant_role_and_object_authorization_matrix() -> None:
    url = os.environ.get("RULETWIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("RULETWIN_TEST_DATABASE_URL is not configured")
    await seed("ruletwin-dev-v1")
    settings = Settings(
        environment="test",
        database_url=url,
        log_level="CRITICAL",
        jwt_secret="integration-only-jwt-secret-000000000000000",
    )
    app = create_app(settings)
    database = Database(url)
    tokens = {
        "author": issue_token(settings, AUTHOR_ID, TENANT_ID),
        "reviewer": issue_token(settings, REVIEWER_ID, TENANT_ID),
        "approver": issue_token(settings, APPROVER_ID, TENANT_ID),
        "auditor": issue_token(settings, AUDITOR_ID, TENANT_ID),
        "foreign_reviewer": issue_token(settings, SECOND_REVIEWER_ID, SECOND_TENANT_ID),
        "foreign_auditor": issue_token(settings, SECOND_AUDITOR_ID, SECOND_TENANT_ID),
    }
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            unauthenticated = await client.get(f"/v1/simulations/{uuid.uuid4()}")
            assert unauthenticated.status_code == 401

            denied_rule = await client.post(
                f"/v1/tenants/{TENANT_ID}/rule-versions",
                headers=_headers(tokens["reviewer"], idempotency=True),
                json={
                    "definition_id": str(RULE_DEFINITION_ID),
                    "family": "rounding",
                    "effective_from": "2026-10-01",
                    "effective_until": None,
                    "timezone": "UTC",
                    "rule": {"increment_minor_units": 9, "mode": "half_up"},
                    "dependency_version_ids": [],
                },
            )
            assert denied_rule.status_code == 404

            candidate = await client.post(
                f"/v1/tenants/{TENANT_ID}/rule-versions",
                headers=_headers(tokens["author"], idempotency=True),
                json={
                    "definition_id": str(RULE_DEFINITION_ID),
                    "family": "rounding",
                    "effective_from": "2026-10-01",
                    "effective_until": None,
                    "timezone": "UTC",
                    "rule": {"increment_minor_units": 9, "mode": "half_up"},
                    "dependency_version_ids": [],
                },
            )
            assert candidate.status_code == 201
            requested = await client.post(
                "/v1/simulations",
                headers=_headers(tokens["author"], idempotency=True),
                json={
                    "tenant_id": str(TENANT_ID),
                    "baseline_rule_version_id": str(BASELINE_RULE_VERSION_ID),
                    "candidate_rule_version_id": candidate.json()["id"],
                    "dataset_manifest_id": str(DATASET_ID),
                    "engine_version": "rounding-engine-v1",
                    "risk_policy_version_id": str(POLICY_ID),
                },
            )
            assert requested.status_code == 202
            simulation_id = requested.json()["id"]

            foreign = await client.get(
                f"/v1/simulations/{simulation_id}",
                headers=_headers(tokens["foreign_reviewer"]),
            )
            absent = await client.get(
                f"/v1/simulations/{uuid.uuid4()}",
                headers=_headers(tokens["foreign_reviewer"]),
            )
            assert foreign.status_code == absent.status_code == 404
            assert foreign.json()["code"] == absent.json()["code"] == "not-found"
            assert foreign.json()["detail"] == absent.json()["detail"]

            same_tenant = await client.get(
                f"/v1/simulations/{simulation_id}",
                headers=_headers(tokens["reviewer"]),
            )
            assert same_tenant.status_code == 200

            async with database.session() as session, session.begin():
                claimed = await claim_one(session, lease_owner="authz-worker", lease_seconds=30)
            assert claimed is not None
            async with database.session() as session, session.begin():
                assert (
                    await process_simulation_event(session, claimed, worker_id="authz-worker")
                    == "completed"
                )

            completed = await client.get(
                f"/v1/simulations/{simulation_id}",
                headers=_headers(tokens["reviewer"]),
            )
            impact = await client.get(
                f"/v1/simulations/{simulation_id}/impact",
                headers=_headers(tokens["reviewer"]),
            )
            assert completed.status_code == impact.status_code == 200

            denied_approval = await client.post(
                f"/v1/simulations/{simulation_id}/approvals",
                headers={
                    **_headers(tokens["author"], idempotency=True),
                    "If-Match": f'"{completed.json()["version"]}"',
                },
                json={
                    "result_checksum": impact.json()["result_checksum"],
                    "policy_version_id": str(POLICY_ID),
                    "decision": "approve",
                },
            )
            assert denied_approval.status_code == 404

            approval = await client.post(
                f"/v1/simulations/{simulation_id}/approvals",
                headers={
                    **_headers(tokens["reviewer"], idempotency=True),
                    "If-Match": f'"{completed.json()["version"]}"',
                },
                json={
                    "result_checksum": impact.json()["result_checksum"],
                    "policy_version_id": str(POLICY_ID),
                    "decision": "approve",
                },
            )
            assert approval.status_code == 201
            gate = await client.post(
                "/v1/release-gates/evaluate",
                headers=_headers(tokens["approver"], idempotency=True),
                json={
                    "simulation_id": simulation_id,
                    "approval_id": approval.json()["id"],
                    "result_checksum": impact.json()["result_checksum"],
                    "policy_version_id": str(POLICY_ID),
                },
            )
            assert gate.status_code == 201
            assert gate.json()["decision"] == "block"

            audit = await client.get("/v1/audit-events", headers=_headers(tokens["auditor"]))
            foreign_audit = await client.get(
                "/v1/audit-events", headers=_headers(tokens["foreign_auditor"])
            )
            assert audit.status_code == foreign_audit.status_code == 200
            assert audit.json()["items"]
            assert all(item["tenant_id"] == str(TENANT_ID) for item in audit.json()["items"])
            assert all(
                item["tenant_id"] == str(SECOND_TENANT_ID) for item in foreign_audit.json()["items"]
            )
    finally:
        await database.dispose()
        await app.state.database.dispose()
