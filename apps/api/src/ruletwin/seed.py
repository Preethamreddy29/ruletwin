import argparse
import asyncio
import uuid

from sqlalchemy import text

from ruletwin.config import get_settings
from ruletwin.db.database import Database

NAMESPACE = uuid.UUID("8ba28604-8eb4-59df-926c-68e814b89b47")


async def seed(seed_value: str) -> None:
    settings = get_settings()
    database = Database(settings.database_url)
    tenant_id = uuid.uuid5(NAMESPACE, f"{seed_value}:tenant:novabill-sandbox")
    user_id = uuid.uuid5(NAMESPACE, f"{seed_value}:user:{settings.synthetic_user_email}")
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
                {"id": tenant_id},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO users (id, email, display_name)
                    VALUES (:id, :email, 'NovaBill Analyst')
                    ON CONFLICT (email) DO NOTHING
                    """
                ),
                {"id": user_id, "email": settings.synthetic_user_email},
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
            for role in ("author", "reviewer"):
                await session.execute(
                    text(
                        """
                        INSERT INTO user_tenant_roles (tenant_id, user_id, role_code)
                        VALUES (:tenant_id, :user_id, :role)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"tenant_id": tenant_id, "user_id": user_id, "role": role},
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
