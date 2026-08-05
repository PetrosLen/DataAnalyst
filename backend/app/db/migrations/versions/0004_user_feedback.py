"""user_feedback (thumbs up/down, closed/wrong-info flags per venue)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "recommendation_event_id",
            sa.BigInteger(),
            sa.ForeignKey("recommendation_events.id"),
            nullable=True,
        ),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("feedback_type", sa.String(), nullable=False),
        sa.Column("free_text", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "feedback_type IN ('thumbs_up', 'thumbs_down', 'closed', 'wrong_info', 'love_it')",
            name="ck_user_feedback_feedback_type",
        ),
    )
    op.create_index("idx_user_feedback_venue", "user_feedback", ["venue_id"])
    op.create_index("idx_user_feedback_type", "user_feedback", ["feedback_type"])


def downgrade() -> None:
    op.drop_table("user_feedback")
