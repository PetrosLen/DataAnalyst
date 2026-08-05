"""user_feedback.audience (self-declared gender/theme at feedback time)

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_feedback", sa.Column("audience", sa.String(), nullable=True))
    op.create_check_constraint(
        "ck_user_feedback_audience",
        "user_feedback",
        "audience IN ('male', 'female', 'other')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_feedback_audience", "user_feedback", type_="check")
    op.drop_column("user_feedback", "audience")
