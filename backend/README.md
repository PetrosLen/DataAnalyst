# Where to? — Backend

FastAPI + PostgreSQL/PostGIS backend. Βλ. `docs/where-to/PRODUCT_DESIGN.md` για το πλήρες product/technical design.

## Local setup

```bash
# 1. Postgres + PostGIS (Docker)
docker compose -f ../infra/docker-compose.yml up -d

# 2. Python env
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Env vars
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Run the API
uvicorn app.main:app --reload
```

API στο `http://localhost:8000`, health check στο `GET /api/v1/health`, DB connectivity check στο `GET /api/v1/health/db`.

## Migrations

```bash
# Νέα migration μετά από αλλαγή σε μοντέλα (app/db/models/)
alembic revision --autogenerate -m "περιγραφή"

# Εφαρμογή
alembic upgrade head

# Rollback ένα βήμα πίσω
alembic downgrade -1
```

## Τρέχον schema (migrations `0001_core_schema`, `0002_search_recommendation_logs`, `0003_confidence_audits`)

Καλύπτει τα "core" tables του Week 1 (`city_areas`, `categories`, `tags`, `admin_users`, `venues`,
`venue_categories`, `venue_sources`, `venue_hours`, `venue_tags`, `venue_signals`) plus
`search_logs`/`recommendation_events` (Week 2, για το `/search` endpoint) plus `confidence_audits`
(audit trail για admin edits). Οι υπόλοιποι πίνακες του πλήρους schema (`user_feedback`,
`sponsored_placements`, `content_pages`, `update_jobs`, `venue_media`, `venue_reviews_internal`,
`user_submitted_corrections`, `duplicate_candidates`, `recommendation_engine_config`) θα
προστεθούν σε επόμενα migrations καθώς χτίζεται το αντίστοιχο functionality (βλ. backlog στο
`docs/where-to/PRODUCT_DESIGN.md` §20.F). Το πλήρες σχήμα-στόχος υπάρχει ήδη ως reference στο
`docs/where-to/schema.sql`.

## Seed data

```bash
python -m app.ingestion.seed_loader
```

Διαβάζει όλα τα YAML αρχεία στο `app/ingestion/seed_data/` και κάνει upsert (idempotent,
matched by slug — ξανατρέξιμο χωρίς duplicates) city_areas/categories/tags/venues.

Το πρώτο batch (`thessaloniki_seed_001.yaml`, 10 venues σε Θεσσαλονίκη — bars/cafes για ήσυχο
ποτό + date spots) προήλθε από web research (όχι επίσκεψη/τηλέφωνο), γι' αυτό:
- Όλα μπαίνουν με `status="pending"` — **δεν** είναι public μέχρι να τα εγκρίνει admin.
- `overall_confidence` χαμηλό-μέτριο (0.35-0.45) και `venue_sources.source_type="claude_assisted"`
  με τα URLs των πηγών.
- `venue_hours` υπάρχουν ΜΟΝΟ όπου βρέθηκε ρητά δηλωμένο ωράριο· τα υπόλοιπα venues δεν έχουν
  καθόλου ωράριο καταχωρημένο (= άγνωστο, όχι εικασία).
- Όσα venues έχουν `geo_precision: district` στο YAML δεν βρέθηκε η ακριβής διεύθυνσή τους σε
  OpenStreetMap — οι συντεταγμένες είναι το κέντρο της γειτονιάς, όχι το ακριβές σημείο, και
  χρειάζονται GPS pin επιβεβαίωση πριν εγκριθούν.

**Επόμενο βήμα (χειροκίνητο, admin):** τηλεφωνική επιβεβαίωση/επίσκεψη ανά venue (ωράριο,
ακριβής τοποθεσία, τιμές) πριν αλλάξει το `status` σε `active`. Μέχρι να υπάρχει venue review
queue στο admin panel, αυτό γίνεται με απευθείας UPDATE στη βάση.

## Recommendation engine (`/search`)

`app/recommendation/` implements the deterministic scoring pipeline from
`docs/where-to/PRODUCT_DESIGN.md` §7: candidate generation (PostGIS `ST_DWithin`) →
scoring (intent/distance/open-now/budget/vibe/context, confidence-penalized) → MMR-style
diversity re-ranking → fallback relaxation when too few candidates are found. Exposed via
`POST /api/v1/search`, which also logs every search + ranked result to `search_logs` /
`recommendation_events` (the score breakdown is what powers "Δες γιατί προτάθηκε").

Example request:

```bash
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "lat": 40.6301, "lon": 22.9440,
    "intent_category_slug": "bar",
    "mobility": "walk",
    "preferred_tag_slugs": ["quiet"]
  }'
```

Only `status="active"` venues are ever returned. Venue detail: `GET /api/v1/venues/{slug}`.

## Admin panel API (`/admin/*`)

HTTP Basic Auth, checked against `admin_users` (bcrypt password hash). Create your own admin user:

```bash
python -m app.scripts.create_admin_user founder@example.com --role owner
```

Endpoints (all require auth):
- `GET /api/v1/admin/venues?status=pending&search=...` — list/filter venues (the review queue —
  default sort surfaces lowest-confidence first)
- `GET /api/v1/admin/venues/{id}` — full detail incl. tags + sources (unlike the public endpoint,
  works for any status)
- `PATCH /api/v1/admin/venues/{id}` — partial update of any editable field, including `status`
  (this is how a `pending` venue becomes `active`, i.e. public). Every changed field is logged to
  `confidence_audits` (old/new value, who, when). Approving (`status` → `active`) auto-stamps
  `last_verified_at`.

```bash
curl -u founder@example.com -X PATCH http://localhost:8000/api/v1/admin/venues/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "active", "overall_confidence": 0.8}'
```

Not built yet: venue creation via API (use the seed loader), tag/hours editing (still DB-direct),
and the low-confidence/stale/duplicate queues from the design doc (`§11`) — those are just
`GET /admin/venues` with different filters for now, no dedicated views.

## Tests

```bash
pytest
```

Runs both pure unit tests (`tests/recommendation/` — scoring/diversity math, no DB needed) and
DB-backed integration tests (`tests/test_search_api.py` — hits a real Postgres/PostGIS instance
via `DATABASE_URL`, wrapped in a transaction that's rolled back after each test so nothing
persists).
