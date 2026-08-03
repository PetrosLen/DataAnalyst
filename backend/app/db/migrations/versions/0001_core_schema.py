"""core schema: city_areas, categories, tags, admin_users, venues + facts (hours, tags, signals, sources)

Revision ID: 0001
Revises:
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "city_areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326),
            nullable=True,
        ),
        sa.UniqueConstraint("slug"),
    )
    # Σημείωση: το GIST index στη γεωμετρία (idx_city_areas_geometry) δημιουργείται
    # αυτόματα από το GeoAlchemy2 (spatial_index=True default) κατά το create_table.

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tag_type", sa.String(), nullable=False),
        sa.Column("icon", sa.String(), nullable=True),
        sa.UniqueConstraint("slug"),
        sa.CheckConstraint(
            "tag_type IN ('vibe', 'amenity', 'audience')", name="ck_tags_tag_type"
        ),
    )

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_admin_users_role"),
    )

    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description_short", sa.String(), nullable=True),
        sa.Column("description_long", sa.String(), nullable=True),
        sa.Column(
            "geom", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=False
        ),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city_area_id", sa.Integer(), sa.ForeignKey("city_areas.id"), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("instagram_url", sa.String(), nullable=True),
        sa.Column("price_level", sa.SmallInteger(), nullable=True),
        sa.Column(
            "primary_category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column(
            "overall_confidence",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("slug"),
        sa.CheckConstraint("price_level BETWEEN 1 AND 4", name="ck_venues_price_level"),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'inactive', 'unverified', 'merged')",
            name="ck_venues_status",
        ),
        sa.CheckConstraint(
            "overall_confidence BETWEEN 0 AND 1", name="ck_venues_overall_confidence"
        ),
    )
    # Σημείωση: το GIST index στη γεωμετρία (idx_venues_geom) δημιουργείται αυτόματα
    # από το GeoAlchemy2 (spatial_index=True default) κατά το create_table.
    op.create_index("idx_venues_status", "venues", ["status"])
    op.create_index("idx_venues_primary_category", "venues", ["primary_category_id"])
    op.create_index(
        "idx_venues_name_trgm",
        "venues",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    op.create_table(
        "venue_categories",
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "category_id", sa.Integer(), sa.ForeignKey("categories.id"), primary_key=True
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "venue_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=True),
        sa.Column(
            "reliability_score", sa.Numeric(3, 2), nullable=False, server_default="0.5"
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_by", sa.Integer(), sa.ForeignKey("admin_users.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "source_type IN ('google_places', 'manual_visit', 'instagram', 'website', "
            "'phone_call', 'user_submission', 'claude_assisted')",
            name="ck_venue_sources_source_type",
        ),
        sa.CheckConstraint(
            "reliability_score BETWEEN 0 AND 1", name="ck_venue_sources_reliability_score"
        ),
    )
    op.create_index("idx_venue_sources_venue", "venue_sources", ["venue_id"])
    op.create_index("idx_venue_sources_type", "venue_sources", ["source_type"])

    op.create_table(
        "venue_hours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=True),
        sa.Column("close_time", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0.5"),
        sa.Column(
            "source_id", sa.Integer(), sa.ForeignKey("venue_sources.id"), nullable=True
        ),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_venue_hours_day_of_week"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_venue_hours_confidence"),
    )
    op.create_index("idx_venue_hours_venue_day", "venue_hours", ["venue_id", "day_of_week"])
    op.create_index(
        "idx_venue_hours_active",
        "venue_hours",
        ["venue_id"],
        postgresql_where=sa.text("valid_to IS NULL"),
    )

    op.create_table(
        "venue_tags",
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id"), primary_key=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0.5"),
        sa.Column(
            "source_id", sa.Integer(), sa.ForeignKey("venue_sources.id"), nullable=True
        ),
        sa.Column("assigned_by", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_venue_tags_confidence"),
        sa.CheckConstraint(
            "assigned_by IN ('admin', 'claude_suggested', 'user_feedback')",
            name="ck_venue_tags_assigned_by",
        ),
    )
    op.create_index("idx_venue_tags_confidence", "venue_tags", ["confidence"])

    op.create_table(
        "venue_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("signal_type", sa.String(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0.5"),
        sa.Column(
            "source_id", sa.Integer(), sa.ForeignKey("venue_sources.id"), nullable=True
        ),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_venue_signals_confidence"),
    )
    op.create_index("idx_venue_signals_venue_type", "venue_signals", ["venue_id", "signal_type"])


def downgrade() -> None:
    op.drop_table("venue_signals")
    op.drop_table("venue_tags")
    op.drop_table("venue_hours")
    op.drop_table("venue_sources")
    op.drop_table("venue_categories")
    op.drop_table("venues")
    op.drop_table("admin_users")
    op.drop_table("tags")
    op.drop_table("categories")
    op.drop_table("city_areas")
