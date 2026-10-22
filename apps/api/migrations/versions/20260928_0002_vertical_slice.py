"""Create Phase 3 first vertical slice data model.

Revision ID: 20260928_0002
Revises: 20260927_0001
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260928_0002"
down_revision: str | None = "20260927_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def _identity_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "rule_definitions",
        *_identity_columns(),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key"),
    )
    op.create_table(
        "rule_versions",
        *_identity_columns(),
        sa.Column("definition_id", UUID, nullable=False),
        sa.Column("family", sa.String(40), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(40), nullable=False),
        sa.Column("rule", JSONB, nullable=False),
        sa.Column("canonical_rule", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(71), nullable=False),
        sa.Column("authored_by", UUID, nullable=False),
        sa.CheckConstraint("family = 'rounding'", name="ck_phase3_rule_family"),
        sa.CheckConstraint(
            "effective_until IS NULL OR effective_until > effective_from",
            name="ck_rule_effective_range",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["definition_id"], ["rule_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["authored_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "checksum"),
    )
    op.create_index(
        "ix_rule_versions_tenant_definition", "rule_versions", ["tenant_id", "definition_id"]
    )
    op.create_table(
        "dataset_manifests",
        *_identity_columns(),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("generator_version", sa.String(60), nullable=False),
        sa.Column("event_schema_version", sa.String(60), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(71), nullable=False),
        sa.Column("created_by", UUID, nullable=False),
        sa.CheckConstraint("event_count > 0 AND event_count <= 100000", name="ck_dataset_count"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "checksum"),
    )
    op.create_table(
        "business_events",
        *_identity_columns(),
        sa.Column("dataset_manifest_id", UUID, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("checksum", sa.String(71), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["dataset_manifest_id"], ["dataset_manifests.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_manifest_id", "sequence"),
    )
    op.create_table(
        "risk_policies",
        *_identity_columns(),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("financial_delta_threshold_minor_units", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(71), nullable=False),
        sa.CheckConstraint(
            "financial_delta_threshold_minor_units >= 0", name="ck_policy_threshold"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "version"),
    )
    op.create_table(
        "simulations",
        *_identity_columns(),
        sa.Column("baseline_rule_version_id", UUID, nullable=False),
        sa.Column("candidate_rule_version_id", UUID, nullable=False),
        sa.Column("dataset_manifest_id", UUID, nullable=False),
        sa.Column("engine_version", sa.String(60), nullable=False),
        sa.Column("risk_policy_version_id", UUID, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("requested_by", UUID, nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("result_checksum", sa.String(71), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('requested','queued','running','completed','failed','cancelled')",
            name="ck_simulation_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["baseline_rule_version_id"], ["rule_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["candidate_rule_version_id"], ["rule_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["dataset_manifest_id"], ["dataset_manifests.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["risk_policy_version_id"], ["risk_policies.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "requested_by", "idempotency_key"),
    )
    op.create_index("ix_simulations_tenant_status", "simulations", ["tenant_id", "status"])
    op.create_table(
        "simulation_runs",
        *_identity_columns(),
        sa.Column("simulation_id", UUID, nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("worker_id", sa.String(120), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_checksum", sa.String(71), nullable=True),
        sa.CheckConstraint("status IN ('running','completed','failed')", name="ck_run_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("simulation_id", "attempt"),
    )
    op.create_table(
        "outcomes",
        *_identity_columns(),
        sa.Column("simulation_run_id", UUID, nullable=False),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("baseline", JSONB, nullable=False),
        sa.Column("candidate", JSONB, nullable=False),
        sa.Column("financial_delta_minor_units", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["simulation_run_id"], ["simulation_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("simulation_run_id", "event_sequence"),
    )
    op.create_table(
        "impact_deltas",
        *_identity_columns(),
        sa.Column("simulation_id", UUID, nullable=False),
        sa.Column("summary", JSONB, nullable=False),
        sa.Column("checksum", sa.String(71), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("simulation_id"),
    )
    op.create_table(
        "risk_evaluations",
        *_identity_columns(),
        sa.Column("simulation_id", UUID, nullable=False),
        sa.Column("policy_version_id", UUID, nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("reasons", JSONB, nullable=False),
        sa.Column("checksum", sa.String(71), nullable=False),
        sa.CheckConstraint("decision IN ('allow','block','error')", name="ck_risk_decision"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["policy_version_id"], ["risk_policies.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("simulation_id"),
    )
    op.create_table(
        "approvals",
        *_identity_columns(),
        sa.Column("simulation_id", UUID, nullable=False),
        sa.Column("reviewer_id", UUID, nullable=False),
        sa.Column("result_checksum", sa.String(71), nullable=False),
        sa.Column("policy_version_id", UUID, nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.CheckConstraint("decision IN ('approve','reject')", name="ck_approval_decision"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["policy_version_id"], ["risk_policies.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("simulation_id", "reviewer_id", "idempotency_key"),
    )
    op.create_table(
        "release_gates",
        *_identity_columns(),
        sa.Column("simulation_id", UUID, nullable=False),
        sa.Column("approval_id", UUID, nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("evidence_checksum", sa.String(71), nullable=False),
        sa.Column("reasons", JSONB, nullable=False),
        sa.CheckConstraint("decision IN ('allow','block')", name="ck_gate_decision"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approval_id"], ["approvals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("simulation_id", "approval_id"),
    )
    op.create_table(
        "audit_events",
        *_identity_columns(),
        sa.Column("actor_id", UUID, nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("object_type", sa.String(60), nullable=False),
        sa.Column("object_id", UUID, nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("correlation_id", UUID, nullable=False),
        sa.Column("causation_id", UUID, nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_tenant_created", "audit_events", ["tenant_id", "created_at", "id"])
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ruletwin_app"
    )
    op.execute("REVOKE UPDATE, DELETE ON audit_events FROM ruletwin_app")


def downgrade() -> None:
    op.drop_index("ix_audit_tenant_created", table_name="audit_events")
    op.drop_index("ix_simulations_tenant_status", table_name="simulations")
    op.drop_index("ix_rule_versions_tenant_definition", table_name="rule_versions")
    for table in (
        "audit_events",
        "release_gates",
        "approvals",
        "risk_evaluations",
        "impact_deltas",
        "outcomes",
        "simulation_runs",
        "simulations",
        "risk_policies",
        "business_events",
        "dataset_manifests",
        "rule_versions",
    ):
        op.drop_table(table)
    op.drop_table("rule_definitions")
