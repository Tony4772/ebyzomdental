"""core — add users.is_platform_operator.

Platform operators (the SaaS/instance owner) can provision new clinics
when a customer contracts the service. This is intentionally a user
flag, not a clinic-role permission: clinic admins hold ``*`` and must
not inherit platform-level actions.

The earliest user is backfilled as operator so existing installs keep
a working owner account after upgrade.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_platform_operator",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.execute(
        """
        UPDATE users
        SET is_platform_operator = true
        WHERE id = (
            SELECT id FROM users ORDER BY created_at ASC NULLS LAST, id ASC LIMIT 1
        );
        """
    )


def downgrade() -> None:
    op.drop_column("users", "is_platform_operator")
