"""Alembic: SaaS subscription fields + payments table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("subscription_price_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "clinics",
        sa.Column("subscription_period_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "platform_subscription_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="PEN", nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("culqi_charge_id", sa.String(length=64), nullable=True),
        sa.Column("culqi_fee_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sunat_igv_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("net_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payer_email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("culqi_charge_id"),
    )
    op.create_index(
        "ix_platform_subscription_payments_clinic_id",
        "platform_subscription_payments",
        ["clinic_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_subscription_payments_clinic_id",
        table_name="platform_subscription_payments",
    )
    op.drop_table("platform_subscription_payments")
    op.drop_column("clinics", "subscription_period_ends_at")
    op.drop_column("clinics", "subscription_price_cents")
