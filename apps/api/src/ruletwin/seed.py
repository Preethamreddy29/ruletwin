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
from ruletwin.scenario import IDENTITIES, TENANTS


async def seed(seed_value: str) -> None:
    settings = get_settings()
    database = Database(settings.database_url)
    if seed_value != "ruletwin-dev-v1":
        raise ValueError("RuleTwin supports the versioned ruletwin-dev-v1 scenario pack only.")
    baseline_rule = {"increment_minor_units": 1, "mode": "half_up"}
    try:
        async with database.session() as session, session.begin():
            for tenant in TENANTS:
                await session.execute(
                    text("""
                        INSERT INTO tenants (id, slug, display_name)
                        VALUES (:id, :slug, :display_name)
                        ON CONFLICT (slug) DO UPDATE SET display_name=EXCLUDED.display_name
                    """),
                    {"id": tenant.id, "slug": tenant.slug, "display_name": tenant.display_name},
                )
            for identity in IDENTITIES:
                await session.execute(
                    text("""
                        INSERT INTO users (id, email, display_name)
                        VALUES (:id, :email, :display_name)
                        ON CONFLICT (email) DO UPDATE SET display_name=EXCLUDED.display_name
                    """),
                    {
                        "id": identity.id,
                        "email": identity.email,
                        "display_name": identity.display_name,
                    },
                )
            for code, description in (
                ("author", "Creates rule proposals"),
                ("reviewer", "Reviews evidence"),
                ("release_approver", "Makes release-gate decisions"),
                ("auditor", "Reads immutable evidence"),
            ):
                await session.execute(
                    text("""
                        INSERT INTO roles (code, description) VALUES (:code, :description)
                        ON CONFLICT (code) DO UPDATE SET description=EXCLUDED.description
                    """),
                    {"code": code, "description": description},
                )
            await session.execute(
                text("DELETE FROM user_tenant_roles WHERE user_id = ANY(:user_ids)"),
                {"user_ids": [identity.id for identity in IDENTITIES]},
            )
            for identity in IDENTITIES:
                await session.execute(
                    text("""
                        INSERT INTO user_tenant_roles (tenant_id, user_id, role_code)
                        VALUES (:tenant_id, :user_id, :role)
                    """),
                    {
                        "tenant_id": identity.tenant_id,
                        "user_id": identity.id,
                        "role": identity.role,
                    },
                )

            for index, tenant in enumerate(TENANTS):
                event_seed = 314159 if index == 0 else 271828
                events = generate_events(event_seed, 100)
                policy = {"version": "phase3-financial-threshold-v1", "threshold_minor_units": 2}
                author = next(
                    identity
                    for identity in IDENTITIES
                    if identity.tenant_id == tenant.id and identity.role == "author"
                )
                await session.execute(
                    text("""
                        INSERT INTO rule_definitions (id, tenant_id, key, display_name)
                        VALUES (:id, :tenant_id, 'invoice-rounding', 'Invoice rounding')
                        ON CONFLICT (tenant_id, key) DO NOTHING
                    """),
                    {"id": tenant.rule_definition_id, "tenant_id": tenant.id},
                )
                await session.execute(
                    text("""
                        INSERT INTO rule_versions
                            (id, tenant_id, definition_id, family, effective_from, timezone,
                             schema_version, rule, canonical_rule, checksum, authored_by)
                        VALUES
                            (:id, :tenant_id, :definition_id, 'rounding', '2026-01-01', 'UTC',
                             'rounding-rule-v1', CAST(:rule AS jsonb), :canonical_rule,
                             :checksum, :author_id)
                        ON CONFLICT (tenant_id, checksum) DO NOTHING
                    """),
                    {
                        "id": tenant.baseline_rule_version_id,
                        "tenant_id": tenant.id,
                        "definition_id": tenant.rule_definition_id,
                        "rule": canonical_json(baseline_rule),
                        "canonical_rule": canonical_json(baseline_rule),
                        "checksum": checksum(baseline_rule),
                        "author_id": author.id,
                    },
                )
                manifest_checksum = dataset_checksum(event_seed, events)
                await session.execute(
                    text("""
                        INSERT INTO dataset_manifests
                            (id, tenant_id, seed, generator_version, event_schema_version,
                             event_count, checksum, created_by)
                        VALUES (:id, :tenant_id, :seed, :generator_version, :schema_version,
                                100, :checksum, :author_id)
                        ON CONFLICT (tenant_id, checksum) DO NOTHING
                    """),
                    {
                        "id": tenant.dataset_id,
                        "tenant_id": tenant.id,
                        "seed": event_seed,
                        "generator_version": GENERATOR_VERSION,
                        "schema_version": EVENT_SCHEMA_VERSION,
                        "checksum": manifest_checksum,
                        "author_id": author.id,
                    },
                )
                for event in events:
                    await session.execute(
                        text("""
                            INSERT INTO business_events
                                (id, tenant_id, dataset_manifest_id, sequence, payload, checksum)
                            VALUES (:id, :tenant_id, :dataset_id, :sequence,
                                    CAST(:payload AS jsonb), :checksum)
                            ON CONFLICT (dataset_manifest_id, sequence) DO NOTHING
                        """),
                        {
                            "id": uuid.UUID(str(event["event_id"])),
                            "tenant_id": tenant.id,
                            "dataset_id": tenant.dataset_id,
                            "sequence": event["sequence"],
                            "payload": canonical_json(event),
                            "checksum": checksum(event),
                        },
                    )
                await session.execute(
                    text("""
                        INSERT INTO risk_policies
                            (id, tenant_id, version,
                             financial_delta_threshold_minor_units, checksum)
                        VALUES (:id, :tenant_id, :version, 2, :checksum)
                        ON CONFLICT (tenant_id, version) DO NOTHING
                    """),
                    {
                        "id": tenant.policy_id,
                        "tenant_id": tenant.id,
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
