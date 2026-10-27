import argparse
import asyncio
import hashlib
import os
import uuid

from sqlalchemy import text

from ruletwin.application.vertical_slice import append_audit
from ruletwin.config import get_settings
from ruletwin.db.database import Database
from ruletwin.scenario import identity_by_key


def _subject_digest(subject: str) -> str:
    return f"sha256:{hashlib.sha256(subject.encode('utf-8')).hexdigest()}"


def _validated_subject(subject: str) -> str:
    if (
        not 1 <= len(subject) <= 255
        or subject != subject.strip()
        or any(c.isspace() for c in subject)
    ):
        raise ValueError("OIDC subject must be 1-255 characters without whitespace.")
    return subject


async def provision_oidc_subject(
    database_url: str,
    *,
    identity_key: str,
    subject: str,
    approved_by_identity_key: str,
) -> bool:
    """Bind one provider subject to one pre-approved synthetic pilot identity.

    Returns True when a new mapping is written and False for an idempotent repeat.
    Provider roles are deliberately ignored; tenant and role remain database-owned.
    """
    target = identity_by_key(identity_key)
    approver = identity_by_key(approved_by_identity_key)
    if target is None:
        raise ValueError("Unknown pilot identity key.")
    if (
        approver is None
        or approver.tenant_id != target.tenant_id
        or approver.role != "release_approver"
    ):
        raise ValueError("Provisioning requires this tenant's release-approver identity.")
    normalized_subject = _validated_subject(subject)

    database = Database(database_url)
    try:
        async with database.session() as session, session.begin():
            target_row = (
                (
                    await session.execute(
                        text("SELECT id, oidc_subject FROM users WHERE id=:id FOR UPDATE"),
                        {"id": target.id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if target_row is None:
                raise ValueError("Pilot identity has not been seeded.")
            if target_row["oidc_subject"] == normalized_subject:
                return False
            if target_row["oidc_subject"] is not None:
                raise ValueError("Pilot identity is already bound to a different OIDC subject.")

            existing_user = await session.scalar(
                text("SELECT id FROM users WHERE oidc_subject=:subject"),
                {"subject": normalized_subject},
            )
            if existing_user is not None:
                raise ValueError("OIDC subject is already bound to another pilot identity.")

            await session.execute(
                text("UPDATE users SET oidc_subject=:subject WHERE id=:id"),
                {"subject": normalized_subject, "id": target.id},
            )
            await append_audit(
                session,
                tenant_id=target.tenant_id,
                actor_id=approver.id,
                action="identity.oidc_subject.provisioned",
                object_type="user",
                object_id=target.id,
                correlation_id=uuid.uuid4(),
                metadata={"subject_digest": _subject_digest(normalized_subject)},
            )
        return True
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bind an invited OIDC subject to an existing RuleTwin pilot identity."
    )
    parser.add_argument("--identity-key", required=True)
    parser.add_argument("--approved-by-identity-key", required=True)
    parser.add_argument(
        "--subject-env",
        default="RULETWIN_PROVISION_OIDC_SUBJECT",
        help=(
            "Environment variable containing the provider subject; avoids command-history exposure."
        ),
    )
    arguments = parser.parse_args()
    subject = os.environ.get(arguments.subject_env)
    if subject is None:
        raise SystemExit(f"Set {arguments.subject_env} before provisioning.")
    changed = asyncio.run(
        provision_oidc_subject(
            get_settings().database_url,
            identity_key=arguments.identity_key,
            subject=subject,
            approved_by_identity_key=arguments.approved_by_identity_key,
        )
    )
    print("OIDC subject mapping created." if changed else "OIDC subject mapping already exists.")


if __name__ == "__main__":
    main()
