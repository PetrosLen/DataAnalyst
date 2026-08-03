"""venues.google_place_id + venue_media.attribution (Google Places photo enrichment)

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("venues", sa.Column("google_place_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_venues_google_place_id", "venues", ["google_place_id"])
    op.add_column("venue_media", sa.Column("attribution", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("venue_media", "attribution")
    op.drop_constraint("uq_venues_google_place_id", "venues", type_="unique")
    op.drop_column("venues", "google_place_id")
