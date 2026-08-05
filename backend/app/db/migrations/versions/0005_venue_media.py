"""venue_media (photos per venue, license_ok gates public display)

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "venue_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False, server_default="photo"),
        sa.Column(
            "source_id", sa.Integer(), sa.ForeignKey("venue_sources.id"), nullable=True
        ),
        sa.Column("license_ok", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_venue_media_venue", "venue_media", ["venue_id"])


def downgrade() -> None:
    op.drop_table("venue_media")
