"""confidence_audits (audit trail for admin edits to venue facts)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "confidence_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(), nullable=True),
        sa.Column("old_value", sa.String(), nullable=True),
        sa.Column("new_value", sa.String(), nullable=True),
        sa.Column("old_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("new_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("changed_by", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_confidence_audits_entity", "confidence_audits", ["entity_type", "entity_id"]
    )


def downgrade() -> None:
    op.drop_table("confidence_audits")
