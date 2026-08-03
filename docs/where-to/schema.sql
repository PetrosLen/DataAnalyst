-- WHERE TO? — Πρώτο SQL schema draft (MVP)
-- PostgreSQL 15+ με PostGIS extension
-- Βλ. docs/where-to/PRODUCT_DESIGN.md §6 για πλήρη τεκμηρίωση ανά πίνακα.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- για fuzzy name matching σε duplicate detection

-- =========================================================
-- DICTIONARIES
-- =========================================================

CREATE TABLE city_areas (
    id            SERIAL PRIMARY KEY,
    city_id       INTEGER NOT NULL DEFAULT 1, -- MVP: Θεσσαλονίκη = 1 (fixed)
    name          TEXT NOT NULL,
    slug          TEXT NOT NULL UNIQUE,
    geometry      GEOMETRY(POLYGON, 4326)
);
CREATE INDEX idx_city_areas_geometry ON city_areas USING GIST (geometry);

CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    parent_id   INTEGER REFERENCES categories(id),
    icon        TEXT,
    sort_order  INTEGER DEFAULT 0
);

CREATE TABLE tags (
    id        SERIAL PRIMARY KEY,
    slug      TEXT NOT NULL UNIQUE,
    name      TEXT NOT NULL,
    tag_type  TEXT NOT NULL CHECK (tag_type IN ('vibe', 'amenity', 'audience')),
    icon      TEXT
);

-- =========================================================
-- ADMIN USERS
-- =========================================================

CREATE TABLE admin_users (
    id             SERIAL PRIMARY KEY,
    email          TEXT NOT NULL UNIQUE,
    role           TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    password_hash  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- CORE: VENUES
-- =========================================================

CREATE TABLE venues (
    id                  SERIAL PRIMARY KEY,
    slug                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    description_short   TEXT,
    description_long    TEXT,
    geom                GEOMETRY(POINT, 4326) NOT NULL,
    address             TEXT,
    city_area_id        INTEGER REFERENCES city_areas(id),
    phone               TEXT,
    website             TEXT,
    instagram_url       TEXT,
    price_level         SMALLINT CHECK (price_level BETWEEN 1 AND 4),
    primary_category_id INTEGER REFERENCES categories(id),
    status              TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'active', 'inactive', 'unverified', 'merged')),
    overall_confidence  NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (overall_confidence BETWEEN 0 AND 1),
    last_verified_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_venues_geom ON venues USING GIST (geom);
CREATE INDEX idx_venues_status ON venues (status);
CREATE INDEX idx_venues_primary_category ON venues (primary_category_id);
CREATE INDEX idx_venues_name_trgm ON venues USING GIN (name gin_trgm_ops);

CREATE TABLE venue_categories (
    venue_id     INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES categories(id),
    is_primary   BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (venue_id, category_id)
);

-- =========================================================
-- SOURCES (source attribution - referenced by hours/tags/signals/media)
-- =========================================================

CREATE TABLE venue_sources (
    id               SERIAL PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source_type      TEXT NOT NULL CHECK (source_type IN
                       ('google_places', 'manual_visit', 'instagram', 'website',
                        'phone_call', 'user_submission', 'claude_assisted')),
    source_ref       TEXT, -- url ή free-text σημείωση
    reliability_score NUMERIC(3,2) DEFAULT 0.5 CHECK (reliability_score BETWEEN 0 AND 1),
    last_checked_at  TIMESTAMPTZ,
    checked_by       INTEGER REFERENCES admin_users(id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_venue_sources_venue ON venue_sources (venue_id);
CREATE INDEX idx_venue_sources_type ON venue_sources (source_type);

-- =========================================================
-- VERSIONED / CONFIDENCE-BEARING FACTS
-- =========================================================

CREATE TABLE venue_hours (
    id          SERIAL PRIMARY KEY,
    venue_id    INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    open_time   TIME,
    close_time  TIME,
    is_closed   BOOLEAN NOT NULL DEFAULT false,
    valid_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to    TIMESTAMPTZ, -- NULL = τρέχον ενεργό
    confidence  NUMERIC(3,2) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    source_id   INTEGER REFERENCES venue_sources(id)
);
CREATE INDEX idx_venue_hours_venue_day ON venue_hours (venue_id, day_of_week);
CREATE INDEX idx_venue_hours_active ON venue_hours (venue_id) WHERE valid_to IS NULL;

CREATE TABLE venue_tags (
    venue_id    INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id),
    confidence  NUMERIC(3,2) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    source_id   INTEGER REFERENCES venue_sources(id),
    assigned_by TEXT NOT NULL CHECK (assigned_by IN ('admin', 'claude_suggested', 'user_feedback')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (venue_id, tag_id)
);
CREATE INDEX idx_venue_tags_confidence ON venue_tags (confidence);

CREATE TABLE venue_signals (
    id           SERIAL PRIMARY KEY,
    venue_id     INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    signal_type  TEXT NOT NULL, -- noise_level, wifi_quality, outdoor_seating, pet_friendly, parking...
    value        JSONB NOT NULL,
    confidence   NUMERIC(3,2) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    source_id    INTEGER REFERENCES venue_sources(id),
    observed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_venue_signals_venue_type ON venue_signals (venue_id, signal_type);

CREATE TABLE venue_media (
    id          SERIAL PRIMARY KEY,
    venue_id    INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    media_type  TEXT NOT NULL DEFAULT 'photo',
    source_id   INTEGER REFERENCES venue_sources(id),
    license_ok  BOOLEAN NOT NULL DEFAULT false,
    sort_order  INTEGER DEFAULT 0
);
CREATE INDEX idx_venue_media_venue ON venue_media (venue_id);

-- =========================================================
-- INTERNAL QA
-- =========================================================

CREATE TABLE venue_reviews_internal (
    id              SERIAL PRIMARY KEY,
    venue_id        INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    admin_id        INTEGER REFERENCES admin_users(id),
    internal_rating SMALLINT CHECK (internal_rating BETWEEN 1 AND 5),
    notes           TEXT,
    visited_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_venue_reviews_internal_venue ON venue_reviews_internal (venue_id);

-- =========================================================
-- MODERATION / DATA QUALITY
-- =========================================================

CREATE TABLE user_submitted_corrections (
    id                    SERIAL PRIMARY KEY,
    venue_id              INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    field_name            TEXT NOT NULL,
    suggested_value       TEXT,
    submitter_session_id  TEXT,
    status                TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by           INTEGER REFERENCES admin_users(id),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_corrections_status ON user_submitted_corrections (status);

CREATE TABLE duplicate_candidates (
    id               SERIAL PRIMARY KEY,
    venue_id_a       INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    venue_id_b       INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    similarity_score NUMERIC(3,2),
    status           TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    reviewed_by      INTEGER REFERENCES admin_users(id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_duplicate_candidates_status ON duplicate_candidates (status);

CREATE TABLE confidence_audits (
    id             SERIAL PRIMARY KEY,
    entity_type    TEXT NOT NULL, -- 'venue', 'venue_tags', 'venue_hours', 'venue_signals'
    entity_id      INTEGER NOT NULL,
    field_name     TEXT,
    old_value      TEXT,
    new_value      TEXT,
    old_confidence NUMERIC(3,2),
    new_confidence NUMERIC(3,2),
    reason         TEXT,
    changed_by     TEXT NOT NULL, -- 'system', 'claude_suggested', or admin_users.id as text
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_confidence_audits_entity ON confidence_audits (entity_type, entity_id);

-- =========================================================
-- USAGE / RECOMMENDATION LOGS
-- =========================================================

CREATE TABLE search_logs (
    id             BIGSERIAL PRIMARY KEY,
    session_id     TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    filters        JSONB NOT NULL,
    origin_geom    GEOMETRY(POINT, 4326),
    city_area_id   INTEGER REFERENCES city_areas(id),
    result_count   INTEGER
);
CREATE INDEX idx_search_logs_session ON search_logs (session_id);
CREATE INDEX idx_search_logs_created ON search_logs (created_at);

CREATE TABLE recommendation_events (
    id               BIGSERIAL PRIMARY KEY,
    search_log_id    BIGINT NOT NULL REFERENCES search_logs(id) ON DELETE CASCADE,
    venue_id         INTEGER NOT NULL REFERENCES venues(id),
    rank_position    SMALLINT NOT NULL,
    score            NUMERIC(5,4),
    score_breakdown  JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_recommendation_events_search ON recommendation_events (search_log_id);
CREATE INDEX idx_recommendation_events_venue ON recommendation_events (venue_id);

CREATE TABLE user_feedback (
    id                       BIGSERIAL PRIMARY KEY,
    recommendation_event_id  BIGINT REFERENCES recommendation_events(id),
    venue_id                 INTEGER NOT NULL REFERENCES venues(id),
    feedback_type            TEXT NOT NULL CHECK (feedback_type IN
                              ('thumbs_up', 'thumbs_down', 'closed', 'wrong_info', 'love_it')),
    free_text                TEXT,
    session_id               TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_user_feedback_venue ON user_feedback (venue_id);
CREATE INDEX idx_user_feedback_type ON user_feedback (feedback_type);

-- =========================================================
-- MONETIZATION
-- =========================================================

CREATE TABLE sponsored_placements (
    id               SERIAL PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id),
    campaign_name    TEXT NOT NULL,
    placement_type   TEXT NOT NULL CHECK (placement_type IN ('featured_slot', 'category_sponsor', 'banner')),
    start_date       DATE NOT NULL,
    end_date         DATE NOT NULL,
    price            NUMERIC(10,2),
    status           TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'expired')),
    impressions_cap  INTEGER,
    impressions_count INTEGER NOT NULL DEFAULT 0,
    clicks_count     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_sponsored_placements_status ON sponsored_placements (status);
CREATE INDEX idx_sponsored_placements_end_date ON sponsored_placements (end_date);

-- =========================================================
-- CONTENT / SEO
-- =========================================================

CREATE TABLE content_pages (
    id               SERIAL PRIMARY KEY,
    slug             TEXT NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    page_type        TEXT NOT NULL CHECK (page_type IN ('area', 'intent', 'evergreen')),
    body_blocks      JSONB NOT NULL DEFAULT '[]',
    related_venue_ids INTEGER[],
    city_area_id     INTEGER REFERENCES city_areas(id),
    status           TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    seo_meta         JSONB,
    last_reviewed_at TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_content_pages_status ON content_pages (status);

-- =========================================================
-- OPERATIONS
-- =========================================================

CREATE TABLE update_jobs (
    id             BIGSERIAL PRIMARY KEY,
    job_type       TEXT NOT NULL,
    target_ref     TEXT,
    status         TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    result_summary JSONB,
    triggered_by   TEXT NOT NULL -- 'cron', 'manual', or admin_users.id as text
);
CREATE INDEX idx_update_jobs_type ON update_jobs (job_type);
CREATE INDEX idx_update_jobs_status ON update_jobs (status);

CREATE TABLE recommendation_engine_config (
    id          SERIAL PRIMARY KEY,
    weights     JSONB NOT NULL, -- {"w_intent":0.30, "w_distance":0.20, ...}
    active      BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by  INTEGER REFERENCES admin_users(id)
);
CREATE UNIQUE INDEX idx_one_active_config ON recommendation_engine_config (active) WHERE active = true;
