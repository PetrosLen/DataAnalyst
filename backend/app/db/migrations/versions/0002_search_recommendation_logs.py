"""search_logs and recommendation_events (needed for the /search endpoint)

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("filters", postgresql.JSONB(), nullable=False),
        sa.Column(
            "origin_geom",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("city_area_id", sa.Integer(), sa.ForeignKey("city_areas.id"), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=True),
    )
    op.create_index("idx_search_logs_session", "search_logs", ["session_id"])
    op.create_index("idx_search_logs_created", "search_logs", ["created_at"])

    op.create_table(
        "recommendation_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "search_log_id",
            sa.BigInteger(),
            sa.ForeignKey("search_logs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("rank_position", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_recommendation_events_search", "recommendation_events", ["search_log_id"]
    )
    op.create_index("idx_recommendation_events_venue", "recommendation_events", ["venue_id"])


def downgrade() -> None:
    op.drop_table("recommendation_events")
    op.drop_table("search_logs")
