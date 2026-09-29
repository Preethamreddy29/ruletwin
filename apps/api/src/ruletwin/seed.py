import argparse
import asyncio
import uuid

from sqlalchemy import text

from ruletwin.config import get_settings
from ruletwin.db.database import Database
from ruletwin.domain.canonical import canonical_json, checksum
from ruletwin.domain.datasets import (
    EVENT_SCHEMA_VERSION,
    GENERATOR_VERSION,
    dataset_checksum,
    generate_events,
)
from ruletwin.scenario import (
    APPROVER_ID,
    AUTHOR_ID,
    BASELINE_RULE_VERSION_ID,
    DATASET_ID,
    POLICY_ID,
    RULE_DEFINITION_ID,
    TENANT_ID,
)


async def seed(seed_value: str) -> None:
    settings = get_settings()
    database = Database(settings.database_url)
    if seed_value != "ruletwin-dev-v1":
        raise ValueError("Phase 3 supports the versioned ruletwin-dev-v1 scenario pack only.")
    events = generate_events(314159, 100)
    baseline_rule = {"increment_minor_units": 1, "mode": "half_up"}
    policy = {"version": "phase3-financial-threshold-v1", "threshold_minor_units": 2}
    try:
        async with database.session() as session, session.begin():
            await session.execute(
                text(
                    """
                    INSERT INTO tenants (id, slug, display_name)
                    VALUES (:id, 'novabill-sandbox', 'NovaBill Sandbox')
                    ON CONFLICT (slug) DO NOTHING
                    """
                ),
                {"id": TENANT_ID},
            )
            for user_id, email, name in (
                (AUTHOR_ID, settings.synthetic_user_email, "NovaBill Analyst"),
                (APPROVER_ID, "approver@novabill.example", "NovaBill Approver"),
            ):
                await session.execute(
                    text(
                        """
                        INSERT INTO users (id, email, display_name)
                        VALUES (:id, :email, :name)
                        ON CONFLICT (email) DO NOTHING
                        """
                    ),
                    {"id": user_id, "email": email, "name": name},
                )
            for code, description in (
                ("author", "Creates rule proposals"),
                ("reviewer", "Reviews evidence"),
                ("release_approver", "Makes release-gate decisions"),
                ("auditor", "Reads immutable evidence"),
            ):
                await session.execute(
                    text(
                        """
                        INSERT INTO roles (code, description)
                        VALUES (:code, :description)
                        ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description
                        """
                    ),
                    {"code": code, "description": description},
                )
            for user_id, role in (
                (AUTHOR_ID, "author"),
                (AUTHOR_ID, "reviewer"),
                (APPROVER_ID, "reviewer"),
                (APPROVER_ID, "release_approver"),
            ):
                await session.execute(
                    text(
                        """
                        INSERT INTO user_tenant_roles (tenant_id, user_id, role_code)
                        VALUES (:tenant_id, :user_id, :role)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"tenant_id": TENANT_ID, "user_id": user_id, "role": role},
                )
            await session.execute(
                text(
                    """
                    INSERT INTO rule_definitions (id, tenant_id, key, display_name)
                    VALUES (:id, :tenant_id, 'invoice-rounding', 'Invoice rounding')
                    ON CONFLICT (tenant_id, key) DO NOTHING
                    """
                ),
                {"id": RULE_DEFINITION_ID, "tenant_id": TENANT_ID},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO rule_versions
                        (id, tenant_id, definition_id, family, effective_from, timezone,
                         schema_version, rule, canonical_rule, checksum, authored_by)
                    VALUES
                        (:id, :tenant_id, :definition_id, 'rounding', '2026-01-01', 'UTC',
                         'rounding-rule-v1', CAST(:rule AS jsonb), :canonical_rule,
                         :checksum, :author_id)
                    ON CONFLICT (tenant_id, checksum) DO NOTHING
                    """
                ),
                {
                    "id": BASELINE_RULE_VERSION_ID,
                    "tenant_id": TENANT_ID,
                    "definition_id": RULE_DEFINITION_ID,
                    "rule": canonical_json(baseline_rule),
                    "canonical_rule": canonical_json(baseline_rule),
                    "checksum": checksum(baseline_rule),
                    "author_id": AUTHOR_ID,
                },
            )
            manifest_checksum = dataset_checksum(314159, events)
            await session.execute(
                text(
                    """
                    INSERT INTO dataset_manifests
                        (id, tenant_id, seed, generator_version, event_schema_version,
                         event_count, checksum, created_by)
                    VALUES (:id, :tenant_id, 314159, :generator_version, :schema_version,
                            100, :checksum, :author_id)
                    ON CONFLICT (tenant_id, checksum) DO NOTHING
                    """
                ),
                {
                    "id": DATASET_ID,
                    "tenant_id": TENANT_ID,
                    "generator_version": GENERATOR_VERSION,
                    "schema_version": EVENT_SCHEMA_VERSION,
                    "checksum": manifest_checksum,
                    "author_id": AUTHOR_ID,
                },
            )
            for event in events:
                event_id = uuid.UUID(str(event["event_id"]))
                await session.execute(
                    text(
                        """
                        INSERT INTO business_events
                            (id, tenant_id, dataset_manifest_id, sequence, payload, checksum)
                        VALUES (:id, :tenant_id, :dataset_id, :sequence,
                                CAST(:payload AS jsonb), :checksum)
                        ON CONFLICT (dataset_manifest_id, sequence) DO NOTHING
                        """
                    ),
                    {
                        "id": event_id,
                        "tenant_id": TENANT_ID,
                        "dataset_id": DATASET_ID,
                        "sequence": event["sequence"],
                        "payload": canonical_json(event),
                        "checksum": checksum(event),
                    },
                )
            await session.execute(
                text(
                    """
                    INSERT INTO risk_policies
                        (id, tenant_id, version, financial_delta_threshold_minor_units, checksum)
                    VALUES (:id, :tenant_id, :version, 2, :checksum)
                    ON CONFLICT (tenant_id, version) DO NOTHING
                    """
                ),
                {
                    "id": POLICY_ID,
                    "tenant_id": TENANT_ID,
                    "version": policy["version"],
                    "checksum": checksum(policy),
                },
            )
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic synthetic RuleTwin data")
    parser.add_argument("--seed", default="ruletwin-dev-v1")
    arguments = parser.parse_args()
    asyncio.run(seed(arguments.seed))


if __name__ == "__main__":
    main()
