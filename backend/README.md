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

## Τρέχον schema (migration `0001_core_schema`)

Καλύπτει μόνο τα "core" tables του Week 1 του execution plan: `city_areas`, `categories`, `tags`,
`admin_users`, `venues`, `venue_categories`, `venue_sources`, `venue_hours`, `venue_tags`,
`venue_signals`. Οι υπόλοιποι πίνακες του πλήρους schema
(`search_logs`, `recommendation_events`, `user_feedback`, `sponsored_placements`, `content_pages`,
`update_jobs`, `confidence_audits`, `venue_media`, `venue_reviews_internal`,
`user_submitted_corrections`, `duplicate_candidates`, `recommendation_engine_config`) θα προστεθούν
σε επόμενα migrations καθώς χτίζεται το αντίστοιχο functionality (βλ. backlog στο
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

## Tests

```bash
pytest
```
