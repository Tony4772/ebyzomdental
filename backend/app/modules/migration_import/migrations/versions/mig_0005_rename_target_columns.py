"""migration_import — rename ``dentalpin_table`` / ``dentalpin_id`` columns.

The ``migration_import_entity_mappings`` table records, for every imported
source entity, the target row it landed on. Those two columns were named
after the product's former name (DentalPin). Rename them to the current
name (ebyzomdental) so the schema no longer references the old brand. No
data is lost — this is a pure ``RENAME COLUMN``.

Revision ID: mig_0005
Revises: mig_0004
Create Date: 2026-08-16
"""

from collections.abc import Sequence

from alembic import op

revision: str = "mig_0005"
down_revision: str | None = "mig_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "migration_import_entity_mappings",
        "dentalpin_table",
        new_column_name="ebyzomdental_table",
    )
    op.alter_column(
        "migration_import_entity_mappings",
        "dentalpin_id",
        new_column_name="ebyzomdental_id",
    )


def downgrade() -> None:
    op.alter_column(
        "migration_import_entity_mappings",
        "ebyzomdental_table",
        new_column_name="dentalpin_table",
    )
    op.alter_column(
        "migration_import_entity_mappings",
        "ebyzomdental_id",
        new_column_name="dentalpin_id",
    )
