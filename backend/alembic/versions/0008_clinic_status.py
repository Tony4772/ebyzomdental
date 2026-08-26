"""core — add clinics.status for platform lifecycle.

Platform operators can pause or block customer clinics without deleting
fiscal data. ``active`` is the default for existing rows.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
    )


def downgrade() -> None:
    op.drop_column("clinics", "status")
