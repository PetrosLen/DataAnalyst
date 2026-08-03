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

## Τρέχον schema (migrations `0001`-`0005`)

Καλύπτει τα "core" tables του Week 1 (`city_areas`, `categories`, `tags`, `admin_users`, `venues`,
`venue_categories`, `venue_sources`, `venue_hours`, `venue_tags`, `venue_signals`) plus
`search_logs`/`recommendation_events` (Week 2, για το `/search` endpoint) plus `confidence_audits`
(audit trail για admin edits) plus `user_feedback` (thumbs up/down κ.λπ.) plus `venue_media`
(φωτογραφίες, βλ. §Photos παρακάτω). Οι υπόλοιποι πίνακες του πλήρους schema
(`sponsored_placements`, `content_pages`, `update_jobs`, `venue_reviews_internal`,
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

### Audience preference (`preferred_audience`)

Optional field on `SearchRequest`: `"male"`, `"female"`, or `"other"` (the frontend sends whatever
the user picked in its gender/theme gate — see frontend README). It resolves to the `tags` table's
`male-friendly` / `female-friendly` slug (tag_type `audience`) and, **only if a venue actually has
that tag**, adds a small confidence-weighted nudge (`+0.08 * tag_confidence`, folded into the
existing `context` score component) — never a filter, never enough to override intent/distance/
budget. `"other"` (or omitting the field) has zero effect.

**Important: neither tag is currently assigned to any of the 10 seed venues**, so today this is
pure plumbing with no visible effect on results. Deciding whether a specific real bar/cafe skews
toward one audience is a subjective call that needs a human (the founder's judgment, or real usage
data over time) — not something to guess from a venue's name or category. Assigning these tags is
still DB-direct for now (no admin UI for tag editing yet, same gap as venue_hours/other tags).

## Feedback (`POST /feedback`)

Public, no auth. Logs a `user_feedback` row (`thumbs_up` / `thumbs_down` / `closed` /
`wrong_info` / `love_it`, optional free text) against a venue by slug. Per the design doc, this
**never auto-updates venue data** — it's a signal for admin review (visible as `feedback_counts`
on `GET /admin/venues/{id}`), not a source of truth.

```bash
curl -s -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "venue_slug": "thermaikos-bar", "feedback_type": "thumbs_up"}'
```

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

## Photos (`venue_media`)

Every photo row starts with `license_ok=False`, no matter how it was sourced — `GET /venues/{slug}`
(public) only ever returns `photo_urls` where `license_ok=True`. This is deliberate: it's the same
"nothing goes live without a human confirming it" rule the rest of the app follows, applied to
images specifically because of copyright risk (see `PATCH /admin/venues/{id}/media/{id}` below).

**Sourcing status as of this batch:** only **1 of 10** seed venues (Orizontes Roof Garden) has a
photo, sourced from its confirmed official website (`orizontesrestaurant.com`). For the other 9,
no safe source was found — most small independent bars/cafes in the seed only have Instagram/
Facebook presence, which isn't something this pipeline scrapes or hotlinks (against platform ToS,
and URLs there aren't stable). One domain that looked like an official site
(`vogatsikou3.gr`) turned out to be an **expired domain now repurposed as an unrelated online
casino review site** — a reminder to verify page content before trusting a URL, not just that it
resolves.

**The real fix for full photo coverage is the Google Places API** (Place Photos), which requires a
Google Cloud project + billing on the founder's own account — not something this pipeline can set
up unilaterally. Once a `GOOGLE_PLACES_API_KEY` exists, an enrichment script can be added to
`app/ingestion/enrichment/` to pull photos for every venue automatically (still landing as
`license_ok=False` pending admin review, per the rule above).

Admin workflow:
- `GET /api/v1/admin/venues/{id}` → `media: [{id, url, license_ok}]`
- `PATCH /api/v1/admin/venues/{id}/media/{media_id}` with `{"license_ok": true}` → makes a photo
  public; logged to `confidence_audits` (`entity_type="venue_media"`) like any other edit.

## Tests

```bash
pytest
```

Runs both pure unit tests (`tests/recommendation/` — scoring/diversity math, no DB needed) and
DB-backed integration tests (`tests/test_search_api.py` — hits a real Postgres/PostGIS instance
via `DATABASE_URL`, wrapped in a transaction that's rolled back after each test so nothing
persists).
