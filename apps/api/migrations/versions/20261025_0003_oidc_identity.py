"""Add stable OIDC subject mapping for pilot identities.

Revision ID: 20261025_0003
Revises: 20260928_0002
Create Date: 2026-10-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261025_0003"
down_revision: str | None = "20260928_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("oidc_subject", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_users_oidc_subject", "users", ["oidc_subject"])


def downgrade() -> None:
    op.drop_constraint("uq_users_oidc_subject", "users", type_="unique")
    op.drop_column("users", "oidc_subject")
