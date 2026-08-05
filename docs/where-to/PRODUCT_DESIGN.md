# WHERE TO? — Product & Technical Design Document

**Status:** v1 draft — MVP: Θεσσαλονίκη
**Owner:** solo technical founder, με Claude ως AI assistant (όχι source of truth)
**Scope αρχείου:** πλήρης σχεδιασμός προϊόντος, data model, recommendation engine, ingestion, admin, SEO, monetization, analytics, automation, stack, execution plan, ρίσκα, deliverables.

---

## 1. PRODUCT VISION

### Τι ακριβώς είναι
Το **Where to?** είναι ένα **hyperlocal decision engine**: ο χρήστης δίνει context (τοποθεσία, ώρα, mood, budget, παρέα, μετακίνηση, preferences) και το app επιστρέφει 3-10 συγκεκριμένες προτάσεις **με αιτιολόγηση και score**, όχι λίστα καταχωρίσεων προς περιήγηση.

Δεν είναι:
- **Directory** (δεν είναι στόχος να έχει "όλα τα μαγαζιά")
- **Blog / guide** (δεν διαβάζεις άρθρα, παίρνεις απόφαση)
- **Booking app** (δεν κάνει κράτηση, οδηγεί σε directions)
- **E-shop** (δεν πουλάει τίποτα στον τελικό χρήστη)

### Ποιο πρόβλημα λύνει
Η στιγμή "πού να πάμε τώρα;" είναι **decision fatigue σε πραγματικό χρόνο**: Google Maps/TripAdvisor απαιτούν να ξέρεις ήδη τι ψάχνεις (search-first), τα reviews είναι static και δεν απαντούν "είναι ήσυχο ΤΩΡΑ", "είναι ανοιχτό ΤΩΡΑ", "χωράει το budget μας ΤΩΡΑ". Instagram/TikTok δίνουν έμπνευση αλλά όχι φιλτράρισμα κατά context. Το κενό είναι ανάμεσα σε "έμπνευση" και "απόφαση".

### Γιατί δεν είναι απλώς άλλος city guide
Ένας guide σε αφήνει να διαβάσεις. Το Where to? σου δίνει **ranked shortlist με λόγο** ("Προτάθηκε γιατί: ανοιχτό τώρα, 6' με τα πόδια, ήσυχο βάσει feedback, budget fit"), confidence score στα δεδομένα, και κουμπιά **refine-in-place** ("πιο ήσυχα", "πιο φθηνά") αντί για νέο search από την αρχή. Η διαφορά είναι **decision UX vs browsing UX**.

### Utility loop που φέρνει repeat usage
```
Context moment (θέλω να βγω/να δουλέψω/να πάω date)
   → άνοιγμα Where to? (γρήγορο input, <15sec)
   → 3-10 προτάσεις με λόγο
   → επιλογή → directions
   → (προαιρετικό) 1-tap feedback ("καλή πρόταση" / "έκλεισε" / "όχι ήσυχο")
   → βελτιώνει confidence data
   → επόμενη φορά, καλύτερο match, μεγαλύτερη εμπιστοσύνη
```
Η επανάληψη δεν βασίζεται σε "περιεχόμενο να διαβάσεις" αλλά στο ότι **η ανάγκη "πού να πάω τώρα" επαναλαμβάνεται 2-5 φορές/εβδομάδα** ανά ενεργό χρήστη (coffee, βραδινό, date, δουλειά, βόλτα). Κάθε επιτυχημένη πρόταση χτίζει εμπιστοσύνη στο εργαλείο, όχι σε ένα άρθρο.

### Best entry wedge για Θεσσαλονίκη
Ξεκίνα από το **"ήσυχο ποτό / ήσυχο καφέ τώρα"** ως το πιο αιχμηρό wedge:
- Είναι η πιο **συναισθηματικά επείγουσα** στιγμή απόφασης (θες να βγεις τώρα, όχι σε 3 μέρες)
- Είναι **κακά καλυμμένη** από υπάρχοντα εργαλεία (κανείς δεν φιλτράρει "ήσυχο ΤΩΡΑ")
- Έχει **χαμηλό βάθος δεδομένων** ανά venue (δεν χρειάζεσαι μενού, τιμοκατάλογο, reviews βάθους — χρειάζεσαι category+hours+noise signal+vibe tags), άρα είναι το φθηνότερο vertical να χτιστεί σωστά πρώτο.
Μετά επεκτείνεσαι σε date spots (παρόμοιο data need) → φαγητό με παρέα (βαρύτερο data need: budget/ποικιλία) → work-friendly cafes → βόλτα/activity.

**Practical recommendation:** Μην ανοίξεις 5 verticals ταυτόχρονα. Launch με 2 (ήσυχο ποτό/καφέ + date spots), γιατί μοιράζονται το ίδιο data schema (noise, vibe, hours, budget) και σου δίνουν αρκετό όγκο για να δοκιμάσεις το recommendation engine πριν επενδύσεις σε πιο "βαριά" verticals.

**Trade-off:** Λιγότερα verticals = μικρότερο TAM αρχικά, αλλά πολύ μεγαλύτερη ποιότητα ανά πρόταση, που είναι το πραγματικό moat (trust), όχι το εύρος.

---

## 2. USER PERSONAS

| Persona | Goal | Context | Friction σήμερα | Πώς το λύνει το app |
|---|---|---|---|---|
| **Το ζευγάρι "τώρα" (Νίκος & Έλενα, 29-34)** | Θέλουν κάτι *τώρα*, χωρίς σχεδιασμό | Παρασκευή βράδυ, 21:30, στο κέντρο | Google Maps δίνει 40 bars χωρίς φίλτρο "ήσυχο"· scrollάρουν Instagram χωρίς αποτέλεσμα | Filters: mood=ήσυχο, party=couple, time=now → 5 προτάσεις με "ανοιχτό τώρα" + διαδρομή 8' |
| **Remote worker (Δάφνη, 27)** | Ήσυχο cafe με wifi για 3-4 ώρες δουλειάς | Καθημερινή πρωί, laptop, ίσως κλήσεις | Δεν ξέρει ποια cafe έχουν πρίζες/wifi/δεν είναι θορυβώδη το μεσημέρι | Vertical "work-friendly": φίλτρο laptop-friendly + quiet + confidence σε αυτά τα signals |
| **Παρέα value-seekers (5 φοιτητές, 22-25)** | Φαγητό με καλή σχέση ποιότητας/τιμής για 5 άτομα | Κυριακή μεσημέρι, budget-conscious | Δεν εμπιστεύονται reviews, δεν ξέρουν τι "χωράει" σε budget | Budget filter ανά άτομο + group-size signal + "γιατί προτάθηκε: budget fit + καλό για ομάδες" |
| **Επισκέπτης πόλης (Marco, 35, τουρίστας)** | Θέλει κάτι αυθεντικό, όχι tourist trap, κοντά στο ξενοδοχείο | Πρώτη φορά Θεσσαλονίκη, 2 μέρες | TripAdvisor γεμάτο generic/high-price επιλογές | Location-based scoring από την τοποθεσία διαμονής + "local vibe" tag, χωρίς να χρειάζεται να ξέρει περιοχές |
| **Solo βόλτα (Γιώργος, 41)** | Θέλει κάτι διαφορετικό/χαλαρωτικό μόνος του | Κυριακή απόγευμα, χωρίς σχέδιο | Δεν ξέρει τι να κάνει χωρίς παρέα, νιώθει "άσκοπο" να ψάξει | "Surprise me" flow με activity/βόλτα intent + solo-friendly tag |
| **Ad-hoc date planner (Σοφία, 26)** | Θέλει date spot με συγκεκριμένο vibe (ρομαντικό, όχι φασαρία) | Σχεδιάζει 1-2 μέρες πριν, όχι τώρα | Τα "top 10 date spots" άρθρα είναι παλιά/γενικά | Intent=date + advance time picker + vibe tags "ρομαντικό/ήσυχο" με confidence score στα tags |

**Practical recommendation:** Το MVP πρέπει να καλύπτει άριστα τα πρώτα 2 (ζευγάρι-τώρα, remote worker) γιατί είναι τα πιο συχνά use cases με το μικρότερο data requirement. Ο τουρίστας είναι δευτερεύων στόχος (χαμηλότερη προτεραιότητα, expansion candidate).

---

## 3. MVP SCOPE

### Must-have (v1)
- Context input: πόλη (fixed=Θεσσαλονίκη), περιοχή/τοποθεσία (geolocation ή manual pin), ώρα (τώρα/συγκεκριμένη), mood/intent (5 verticals), budget/άτομο, παρέα type, μετακίνηση (πόδια/αμάξι/ΜΜΜ)
- Ranked αποτελέσματα 3-10 με: αιτιολόγηση, score, distance/χρόνος, open-now status, εκτιμώμενο budget, vibe tags, confidence indicator
- Venue detail page (βλ. §5)
- "Δες γιατί προτάθηκε" breakdown
- Refine buttons: "πιο ήσυχα", "πιο οικονομικά", "πιο κοντά"
- Directions button (deep link σε Google/Apple Maps)
- Deterministic ranking engine (χωρίς ML)
- Admin panel: venue CRUD, review queue, confidence management
- Curated seed dataset (150-250 venues, 2 verticals αρχικά)
- Βασικό analytics instrumentation
- Lightweight feedback (thumbs up/down + "έκλεισε/λάθος στοιχεία")
- 1-2 sponsored slots (labeled) — τεχνικά έτοιμο, όχι απαραίτητα ενεργό day 1

### Should-have (v1.x, μέσα στους πρώτους 2-3 μήνες)
- "Surprise me" flow
- Saved/recent searches (local storage, όχι account system)
- Επέκταση σε 3-5 verticals
- Content/landing pages ανά περιοχή×intent (SEO)
- Newsletter/weekly digest (χωρίς σύνδεση με λογαριασμό, μόνο email)
- Weather-aware context modifier

### Future (v2+)
- Λογαριασμοί χρηστών / προσωποποιημένη ιστορία
- Machine learning ranking (μετά από αρκετά real feedback data)
- Πολλαπλές πόλεις
- Native app (μόνο αν το mobile web αποδειχθεί ανεπαρκές)
- Crowdsourced reviews σε βάθος
- Επεκτάσεις σε booking/affiliate

### Things to avoid στο πρώτο release
- **Μην** χτίσεις account/login system πρώτα — προσθέτει friction σε μια χρήση που πρέπει να είναι <30 δευτερόλεπτα
- **Μην** βασιστείς σε crowdsourced data για να "γεμίσει" η βάση — δεν θα υπάρχει όγκος χρηστών day 1
- **Μην** προσπαθήσεις ML ranking χωρίς data — deterministic πρώτα
- **Μην** ανοίξεις σε >2 verticals ταυτόχρονα στο launch
- **Μην** βάλεις ads πριν αποδειχθεί ότι το core value prop δουλεύει (πρώτα trust, μετά monetization surface)
- **Μην** χτίσεις native app

**Trade-off:** Το πιο επικίνδυνο ρίσκο στο MVP δεν είναι τεχνικό, είναι **βάθος δεδομένων vs εύρος**. Προτίμησε 150 venues με πραγματικά καλά, verified δεδομένα από 1000 venues με μέτρια δεδομένα — το recommendation engine είναι τόσο καλό όσο τα δεδομένα του.

---

## 4. CORE USER FLOWS

### Flow A: Home → Filters → Results → Venue Detail → Directions
1. **Home**: μεγάλο CTA "Πού να πάω τώρα;" + quick intent chips (ήσυχο ποτό / date / φαγητό / δουλειά / βόλτα)
2. **Filters** (progressive, όχι ένα μεγάλο form): επιλογή intent (αν δεν επιλέχθηκε ήδη) → time (τώρα default) → company type → budget slider → mobility → (προαιρετικά) extra preferences ως toggles
   - *Edge case:* geolocation denied → fallback σε manual περιοχή picker (dropdown με γειτονιές Θεσσαλονίκης)
   - *Friction point:* πολλά filters = εγκατάλειψη· λύση = smart defaults (time=τώρα, budget=μεσαίο, mobility=πόδια εντός 1.5km) ώστε 1 tap να δίνει ήδη αποτελέσματα
3. **Results**: 3-10 κάρτες, sorted by score, με sticky refine bar
   - *Edge case:* 0 αποτελέσματα πληρούν όλα τα κριτήρια → fallback logic (§7) εμφανίζει relaxed results με ένδειξη "διευρυμένη αναζήτηση"
4. **Venue detail**: πλήρες προφίλ + "γιατί προτάθηκε" + directions CTA
5. **Directions**: deep link σε Google Maps/Apple Maps με προσυμπληρωμένο destination

### Flow B: Home → "Surprise me"
1-tap χωρίς filters → engine επιλέγει intent βάσει ώρας/ημέρας (π.χ. Κυριακή απόγευμα → βόλτα/activity bias) + τυχαιότητα εντός top-scored candidates (weighted random στο top 15, όχι απόλυτο top-1) ώστε να μη δείχνει πάντα το ίδιο.
- *Edge case:* πρώτη χρήση χωρίς κανένα context → ζητά μόνο τοποθεσία, όλα τα άλλα defaults.

### Flow C: Results → Refine Intent
Κουμπιά "πιο ήσυχα" / "πιο οικονομικά" / "πιο κοντά" **δεν ανοίγουν νέο search** — ξαναρέχουν το ranking με προσαρμοσμένα βάρη (π.χ. weight noise_level↑) πάνω στο ίδιο candidate pool, με animated re-sort (perceived ταχύτητα, όχι νέο loading).
- *Edge case:* διαδοχικά refinements να μην "κλειδώνουν" σε 0 results — κάθε refine κρατά minimum 3 results, relaxing κάτι άλλο αν χρειαστεί.

### Flow D: Venue Page → Feedback
Μετά από directions click ή μετά από χρόνο στη σελίδα, discreet prompt (όχι modal-block): "Ήταν καλή πρόταση;" 👍/👎 + optional "κάτι δεν είναι σωστό;" (έκλεισε / λάθος ώρες / λάθος vibe).
- Feedback **δεν** ενημερώνει αυτόματα τη βάση — πάει σε `user_feedback` και `search_logs`/`recommendation_events` για aggregate signal, με χειροκίνητο review αν συσσωρευτούν αρνητικά σήματα.

### Flow E: Saved / Recent Searches
Χωρίς account: local storage-based "πρόσφατες αναζητήσεις" (τελευταίες 5) εμφανίζονται στο home ως quick-repeat chips. "Saved venues" = lightweight local bookmarks (device-based), όχι server-side account.
- *Trade-off:* χάνεται cross-device sync, αλλά αποφεύγεται το friction/κόστος του account system στο MVP. Αν αργότερα αποδειχθεί ζήτηση, προστίθεται προαιρετικό magic-link email account.

**Practical recommendation:** Το πιο σημαντικό flow να τελειοποιηθεί πρώτο είναι το A (home→results→directions) γιατί είναι το 90% της χρήσης. Το "surprise me" και refine buttons είναι διαφοροποιητικά αλλά δευτερεύοντα.

---

## 5. INFORMATION ARCHITECTURE

### Pages / Views (mobile-first)
```
/ (Home)                          → CTA + quick intent chips + recent searches
/results                          → filtered results list (state στο URL query params)
/venue/[slug]                     → venue detail
/pou-na-pao-tora/[intent]         → dynamic "πού να πάω τώρα" landing (SEO)
/thessaloniki/[area]/[intent]     → area×intent landing pages (SEO)
/guides/[slug]                    → evergreen content pages
/about, /contact, /privacy, /terms
/admin/*                          → admin panel (auth-protected, ξεχωριστό sub-app)
```

### Navigation
Mobile-first = **καμία persistent top nav με πολλά items**. Bottom-anchored primary CTA ("Πού να πάω;") πάντα ορατό. Minimal header (λογότυπο + πόλη selector, μελλοντικά). Καμία hamburger menu στο MVP — το app έχει ένα κύριο task.

### Venue Detail — sections
1. Hero: όνομα, category, βασικά vibe tags, confidence badge
2. "Γιατί προτάθηκε" (μόνο αν ήρθε από results, context-aware)
3. Status: ανοιχτό/κλειστό τώρα + ωράριο
4. Distance/χρόνος μετάβασης + CTA "Οδηγίες"
5. Budget εκτίμηση (€/€€/€€€)
6. Vibe & amenities tags (ήσυχο, pet-friendly, laptop-friendly, εξωτερικός χώρος, κλπ)
7. Φωτογραφίες (αν υπάρχουν, με source attribution)
8. Sponsored badge (αν εφαρμόζεται, ξεκάθαρα διαχωρισμένο)
9. Feedback micro-prompt
10. "Παρόμοιες προτάσεις" (ίδιο vertical/περιοχή)

### Admin Panel — top-level sections
```
/admin/dashboard                  → επισκόπηση metrics + alerts
/admin/venues                     → CRUD, search, filters
/admin/queues/low-confidence
/admin/queues/stale
/admin/queues/source-verification
/admin/queues/user-corrections
/admin/queues/duplicates
/admin/sponsorships
/admin/content-pages
/admin/analytics
/admin/logs (audit trail)
/admin/settings (users/roles)
```

**Practical recommendation:** Κράτα το IA επίπεδο (max 2 clicks βάθος) στο public app. Βάθος = friction σε mobile context "έξω, βιαστικά".

---

## 6. DATA MODEL (PostgreSQL + PostGIS)

Αρχές: **κάθε γεγονός αλήθειας έχει source + confidence + timestamp.** Ό,τι επηρεάζει public-facing ranking είναι versionable/auditable.

| Table | Purpose | Βασικά πεδία | Σχέσεις | Indexes | Versioned; | Confidence; | Source attribution |
|---|---|---|---|---|---|---|---|
| **venues** | Κεντρική οντότητα μαγαζιού/σημείου | id, slug, name, description_short, description_long, geom(Point,4326), address, city_area_id, phone, website, instagram_url, price_level(1-4), primary_category_id, status(active/inactive/unverified/merged), overall_confidence, last_verified_at, created_at, updated_at | → city_areas, → categories (primary), ← venue_categories, ← venue_tags, ← venue_hours, ← venue_signals, ← venue_sources | GIST(geom), btree(status), btree(primary_category_id), btree(slug) | Ναι (confidence_audits) | Ναι (overall) | Έμμεσα μέσω venue_sources |
| **categories** | Dictionary κατηγοριών (bar, cafe, restaurant, activity...) | id, slug, name, parent_id, icon, sort_order | ← venue_categories | unique(slug) | Όχι | — | — |
| **venue_categories** | Junction venue↔category (many-to-many) | venue_id, category_id, is_primary | → venues, → categories | unique(venue_id, category_id) | Όχι | — | — |
| **tags** | Dictionary tags (vibe/amenity/audience type) | id, slug, name, tag_type(vibe/amenity/audience), icon | ← venue_tags | unique(slug) | Όχι | — | — |
| **venue_tags** | Venue↔tag με confidence | venue_id, tag_id, confidence(0-1), source_id, assigned_by(admin/claude_suggested/user_feedback), created_at | → venues, → tags, → venue_sources | unique(venue_id, tag_id), btree(confidence) | Ναι (μέσω confidence_audits) | **Ναι, per-tag** | **Ναι** |
| **venue_hours** | Ωράριο ανά ημέρα | venue_id, day_of_week(0-6), open_time, close_time, is_closed, valid_from, valid_to, confidence, source_id | → venues, → venue_sources | idx(venue_id, day_of_week), idx(valid_to) για ενεργά | **Ναι** (valid_from/valid_to = temporal versioning) | **Ναι** | **Ναι** |
| **venue_signals** | Soft attributes: noise_level, wifi_quality, outdoor_seating, pet_friendly, parking, group_friendly κλπ | venue_id, signal_type, value(numeric/bool/enum json), confidence, source_id, observed_at | → venues, → venue_sources | idx(venue_id, signal_type) | Ναι (observed_at ιστορικό) | **Ναι** | **Ναι** |
| **venue_sources** | Από πού προήλθε κάθε στοιχείο | id, venue_id, source_type(google_places/manual_visit/instagram/website/phone_call/user_submission/claude_assisted), source_ref(url/note), reliability_score, last_checked_at, checked_by | → venues | idx(venue_id), idx(source_type) | — | — | **Είναι το ίδιο attribution table** |
| **venue_reviews_internal** | Εσωτερικές σημειώσεις QA ομάδας (όχι public) | id, venue_id, admin_id, internal_rating, notes, visited_at, created_at | → venues, → admin_users | idx(venue_id) | Όχι | Όχι | — |
| **venue_media** | Φωτογραφίες/media | id, venue_id, url, media_type, source_id, license_ok(bool), sort_order | → venues, → venue_sources | idx(venue_id) | Όχι | — | **Ναι** |
| **city_areas** | Γειτονιές/ζώνες Θεσσαλονίκης | id, name, slug, geometry(Polygon,4326), city_id | ← venues, ← content_pages | GIST(geometry) | Όχι | — | — |
| **search_logs** | Κάθε αναζήτηση | id, session_id, created_at, filters(jsonb), origin_geom(Point), city_area_id, result_count | — | idx(session_id), idx(created_at) | — | — | — |
| **recommendation_events** | Κάθε πρόταση που εμφανίστηκε | id, search_log_id, venue_id, rank_position, score, score_breakdown(jsonb), created_at | → search_logs, → venues | idx(search_log_id), idx(venue_id) | — | — | — |
| **user_feedback** | Feedback ανά πρόταση/venue | id, recommendation_event_id, venue_id, feedback_type(thumbs_up/thumbs_down/closed/wrong_info/love_it), free_text, session_id, created_at | → recommendation_events, → venues | idx(venue_id), idx(feedback_type) | — | — | — |
| **user_submitted_corrections** | Διορθώσεις από χρήστες | id, venue_id, field_name, suggested_value, submitter_session_id, status(pending/approved/rejected), reviewed_by, created_at | → venues, → admin_users | idx(status) | — | — | Session-based, όχι identity |
| **duplicate_candidates** | Υποψήφια διπλότυπα | id, venue_id_a, venue_id_b, similarity_score, status(pending/confirmed/rejected), reviewed_by, created_at | → venues (x2) | idx(status) | — | — | — |
| **sponsored_placements** | Χορηγούμενες προβολές | id, venue_id, campaign_name, placement_type(featured_slot/category_sponsor/banner), start_date, end_date, price, status(active/paused/expired), impressions_cap, impressions_count, clicks_count | → venues | idx(status), idx(end_date) | Όχι | — | — |
| **update_jobs** | Log background jobs | id, job_type, target_ref, status(running/success/failed), started_at, finished_at, result_summary(jsonb), triggered_by(cron/manual/admin_id) | — | idx(job_type), idx(status) | — | — | — |
| **confidence_audits** | Ιστορικό αλλαγών confidence/facts | id, entity_type, entity_id, field_name, old_value, new_value, old_confidence, new_confidence, reason, changed_by(system/admin_id/claude_suggested), created_at | polymorphic → venues/tags/hours/signals | idx(entity_type, entity_id) | **Είναι το ίδιο το versioning log** | — | Καταγράφει πηγή αλλαγής |
| **content_pages** | SEO landing/evergreen pages | id, slug, title, page_type(area/intent/evergreen), body_blocks(jsonb), related_venue_ids(int[] ή junction), city_area_id, status(draft/published), seo_meta(jsonb), last_reviewed_at, created_at | → city_areas | unique(slug), idx(status) | Ναι (draft→published states) | — | — |
| **admin_users** | Χρήστες admin panel | id, email, role(owner/editor/viewer), password_hash/oauth_id, created_at | ← venue_reviews_internal, ← confidence_audits | unique(email) | — | — | — |

**Πρόσθετα που κρίνονται απαραίτητα:**
- **`recommendation_engine_config`**: αποθηκεύει τα weights του scoring formula ως versioned config (jsonb) ώστε να αλλάζεις βάρη χωρίς deploy και να κρατάς ιστορικό ποιο config έτρεχε πότε (χρήσιμο για A/B ή debugging περίεργων προτάσεων).
- **`newsletter_subscribers`** (Phase 2): email, subscribed_at, area_preference, status.

**Τι πρέπει να είναι versioned:** venue_hours (temporal validity), venue_tags/venue_signals confidence changes (μέσω confidence_audits), content_pages (draft/published states).
**Τι πρέπει να έχει confidence score:** venue_tags, venue_hours, venue_signals, venues.overall_confidence (aggregate).
**Τι πρέπει να έχει source attribution:** κάθε πίνακας που περιέχει "γεγονός" (hours, tags, signals, media) μέσω venue_sources FK.

**Practical recommendation:** Μην κάνεις normalize σε βαθμό υπερβολής (π.χ. μην φτιάξεις 15 πίνακες dictionary). `venue_signals` ως EAV-style (type/value jsonb) είναι επίτηδες ευέλικτο ώστε να προσθέτεις νέα signals χωρίς migration σε κάθε νέο vertical.

**Trade-off:** Το EAV pattern στο `venue_signals` χάνει κάποιο type-safety στο query layer (χρειάζεται validation στο application layer), αλλά κερδίζεις ταχύτητα επέκτασης σε νέα verticals χωρίς σχήμα migration κάθε φορά.

---

## 7. RECOMMENDATION ENGINE (MVP — deterministic, χωρίς ML)

### Αρχή σχεδιασμού
Ξεκάθαρος, εξηγήσιμος, tunable scoring formula. Το "γιατί προτάθηκε" πρέπει να είναι **κυριολεκτικά το score breakdown**, όχι μαύρο κουτί.

### Pipeline
```
1. Candidate generation (spatial + hard filters)
2. Scoring (weighted formula)
3. Confidence penalty
4. Diversity re-ranking (MMR-style)
5. Fallback relaxation αν <3 αποτελέσματα
```

### 1. Candidate generation
- PostGIS `ST_DWithin(venue.geom, user.geom, radius)` — radius βάσει mobility (π.χ. 1.2km πόδια, 6km αμάξι)
- Hard filters: intent/category match, status='active'
- (Optional hard filter) budget hard-cap αν ο χρήστης το έχει δηλώσει ρητά ως strict

### 2. Scoring formula
```
score = (
    w_intent   * intent_match_score      +   # 0-1
    w_distance * distance_score          +   # 0-1, closer = higher
    w_open     * open_now_score          +   # 0/0.5/1
    w_budget   * budget_fit_score        +   # 0-1
    w_vibe     * vibe_match_score        +   # 0-1
    w_context  * context_modifier_score      # -0.2..+0.2
) * confidence_multiplier
```
Default βάρη (tunable μέσω `recommendation_engine_config`):
`w_intent=0.30, w_distance=0.20, w_open=0.15, w_budget=0.15, w_vibe=0.20`

### Επιμέρους scoring
- **intent_match_score**: 1.0 αν primary_category ταιριάζει ακριβώς με το intent, 0.6 αν secondary category, 0 αλλιώς (hard-filtered ούτως ή άλλως)
- **distance_score**: `max(0, 1 - (distance_km / max_radius_km))` — γραμμική απόσβεση
- **open_now_score**: 1.0 αν ανοιχτό τώρα με confidence≥0.7 στο hours· 0.5 αν ανοιχτό αλλά χαμηλή confidence στα ωράρια (φανερώνεται ως "πιθανώς ανοιχτό")· 0 αν κλειστό (εξαιρείται από default results, εμφανίζεται μόνο σε "δείξε όλα")
- **budget_fit_score**: 1.0 αν price_level εντός του budget range του χρήστη, 0.5 αν 1 επίπεδο έξω, 0 αλλιώς
- **vibe_match_score**: Jaccard-like overlap μεταξύ requested vibe tags και venue_tags, σταθμισμένο με το confidence του κάθε tag: `Σ(matched_tag.confidence) / count(requested_tags)`
- **context_modifier_score**: μικρές προσαρμογές βάσει ώρας/ημέρας/καιρού (π.χ. Κυριακή απόγευμα boost σε "βόλτα/activity" venues, βροχή boost σε indoor/cafe, penalty σε outdoor-only venues)

### Confidence penalty
```
confidence_multiplier = 0.5 + 0.5 * venue.overall_confidence
```
Δηλαδή venue με confidence=0 δεν μηδενίζεται τελείως (0.5x) αλλά υποβαθμίζεται σημαντικά· venue με confidence=1 δεν έχει penalty.

### Diversity rules (MMR-style)
Μετά το αρχικό ranking, re-rank ώστε να αποφευχθούν 10 σχεδόν-ίδιες προτάσεις:
```
selected = [top-1 result]
while len(selected) < N and candidates remain:
    for each candidate c:
        diversity_penalty = max(similarity(c, s) for s in selected)
        adjusted_score = c.score - λ * diversity_penalty
    pick candidate με max adjusted_score
    selected.append(candidate)
```
`similarity(a,b)` = συνδυασμός: ίδια ακριβής κατηγορία (+βάρος), απόσταση μεταξύ τους <200m (+βάρος), overlapping vibe tags (+βάρος). `λ≈0.3`.

### Fallback logic (λίγα δεδομένα)
Αν μετά τα hard filters προκύπτουν <3 candidates:
```
attempt 1: χαλάρωσε radius (+50%)
attempt 2: χαλάρωσε budget strictness (±1 price level)
attempt 3: χαλάρωσε vibe strictness (μείωσε βάρος w_vibe)
αν ακόμα <3: εμφάνισε ό,τι υπάρχει με ένδειξη
   "Λίγα αποτελέσματα βρέθηκαν — διευρύναμε την αναζήτηση"
```
Ποτέ μην επιστρέφεις 0 αποτελέσματα σιωπηλά — πάντα δείξε κάτι + διαφανές μήνυμα relaxation.

### Pseudo-code (πλήρες)
```python
def get_recommendations(user_context, limit=8):
    candidates = query_candidates(
        geom=user_context.location,
        radius_km=radius_for_mobility(user_context.mobility),
        category=user_context.intent,
        status="active",
    )

    relax_level = 0
    while len(candidates) < 3 and relax_level < 3:
        relax_level += 1
        candidates = relax_search(user_context, relax_level)

    scored = []
    for venue in candidates:
        s = compute_score(venue, user_context)
        scored.append((venue, s))

    scored.sort(key=lambda x: x[1].total, reverse=True)
    diversified = diversify(scored, limit=limit, lambda_=0.3)

    return {
        "results": diversified,
        "relaxed": relax_level > 0,
        "relax_level": relax_level,
    }

def compute_score(venue, ctx):
    intent = intent_match_score(venue, ctx.intent)
    distance = distance_score(venue, ctx.location, ctx.max_radius)
    open_now = open_now_score(venue, ctx.time)
    budget = budget_fit_score(venue, ctx.budget)
    vibe = vibe_match_score(venue, ctx.requested_tags)
    context_mod = context_modifier_score(venue, ctx.time, ctx.weather)

    raw = (
        W_INTENT * intent + W_DISTANCE * distance + W_OPEN * open_now +
        W_BUDGET * budget + W_VIBE * vibe + W_CONTEXT * context_mod
    )
    confidence_mult = 0.5 + 0.5 * venue.overall_confidence
    total = raw * confidence_mult

    return ScoreBreakdown(
        total=total, intent=intent, distance=distance, open_now=open_now,
        budget=budget, vibe=vibe, context=context_mod,
        confidence_mult=confidence_mult,
    )
```

**Practical recommendation:** Κράτα το score_breakdown πάντα αποθηκευμένο στο `recommendation_events.score_breakdown` — είναι το θεμέλιο και για debugging και για το μελλοντικό ML dataset.

**Trade-off:** Deterministic ranking είναι λιγότερο "έξυπνο" από ML, αλλά είναι **100% εξηγήσιμο, debug-able, και δουλεύει με μηδενικό training data** — σωστή επιλογή για MVP με μικρό όγκο feedback.

---

## 8. DATA INGESTION STRATEGY

### Πηγές & στάδια
1. **Curated seed dataset** (manual, founder-driven): 150-250 venues σε 2 verticals, επίσκεψη/έρευνα προσωπική ή μέσω Google Places/Instagram, καταχώρηση από admin panel.
2. **Semi-automated enrichment**: Claude διαβάζει raw κείμενο (περιγραφή από Google Places, Instagram bio, website) και προτείνει κατηγοριοποίηση/tags/vibe σε **draft state** — admin εγκρίνει πριν δημοσιευτεί.
3. **Source tracking**: κάθε πεδίο συνδέεται με `venue_sources` row.
4. **Freshness strategy**: `last_verified_at` + confidence decay function (§15) — μετά X ημέρες χωρίς re-verify, confidence μειώνεται αυτόματα, μπαίνει σε stale queue.
5. **Confidence-based update workflow**: χαμηλή confidence → μπαίνει σε review queue → admin verify (τηλέφωνο/επίσκεψη/site check) → confidence reset σε υψηλό με νέο source.
6. **Duplicate detection**: batch job τρέχει trigram similarity σε name + `ST_DWithin` σε geom (<100m) → γεμίζει `duplicate_candidates` → admin αποφασίζει merge/reject.
7. **Data validation**: πριν status='active', υποχρεωτικά: έγκυρο geom, ≥1 category, ≥1 source, hours (ή explicit "άγνωστο ωράριο" flag).
8. **User-submitted corrections**: lightweight "κάτι δεν είναι σωστό;" φόρμα χωρίς login → `user_submitted_corrections`, ποτέ auto-apply.
9. **Moderation pipeline**: ενοποιημένη admin ουρά = low_confidence ∪ stale ∪ pending_corrections ∪ duplicate_candidates, με SLA badges (π.χ. >30 μέρες σε ουρά = κόκκινο flag).

### Τι μπαίνει manually
- Αρχική εισαγωγή venue (όνομα, τοποθεσία, κατηγορία)
- Επιβεβαίωση ωραρίου (τηλεφωνικά/επίσκεψη/επίσημο site)
- Approval οποιασδήποτε πρότασης του Claude πριν γίνει public
- Merge αποφάσεις για duplicates
- Οτιδήποτε επηρεάζει "μόνιμο κλείσιμο" status

### Τι μπορεί να βοηθήσει το Claude να κατηγοριοποιήσει
- Πρόταση category/subcategory από raw περιγραφή
- Πρόταση vibe tags από reviews/κείμενο/φωτογραφίες περιγραφής
- Draft σύντομης περιγραφής (description_short) από πηγαία κείμενα
- Εντοπισμός πιθανών duplicates από ονόματα (fuzzy text reasoning πέρα από trigram)
- Draft SEO copy για content_pages

### Τι δεν πρέπει ΠΟΤΕ να ενημερώνεται αυτόματα χωρίς human review
- Ωράριο λειτουργίας (αλλαγές)
- Μόνιμο κλείσιμο / αλλαγή status
- Διεύθυνση/γεωτοποθεσία
- Price level
- Κατηγορία (αλλαγή primary category μετά το πρώτο publish)
- Οτιδήποτε προκύπτει *αποκλειστικά* από Claude χωρίς πηγαίο κείμενο-αναφορά

**Practical recommendation:** Ξεκίνα με **100% manual seed** για τα πρώτα 100-150 venues — δεν αξίζει να χτίσεις enrichment pipeline πριν έχεις ένα σταθερό schema. Πρόσθεσε Claude-assisted enrichment μόλις το schema σταθεροποιηθεί.

**What to avoid:** Μην εμπιστευτείς scraped δεδομένα (π.χ. Google Places API) ως τελική αλήθεια για ωράριο — είναι γνωστά αναξιόπιστα σε τοπικές επιχειρήσεις στην Ελλάδα. Χρησιμοποίησέ τα ως αρχικό signal με χαμηλό confidence, ποτέ ως verified.

---

## 9. ROLE OF CLAUDE

| Κατηγορία | Concrete task examples | Input | Output format | Strict JSON; | Human review; |
|---|---|---|---|---|---|
| **Architecture help** | Σχεδιασμός schema αλλαγών, review τεχνικών αποφάσεων | Περιγραφή προβλήματος + τρέχον schema | Markdown πρόταση + rationale | Όχι | Πάντα (design decision) |
| **Backend code** | FastAPI endpoints, scoring engine functions, Pydantic models | Spec/user story + σχετικά αρχεία | Python code + σύντομη εξήγηση | Όχι | Ναι, πριν merge |
| **SQL** | CREATE TABLE, migrations, query optimization | Schema + απαίτηση | SQL script | Όχι | Ναι, πριν εφαρμογή σε production DB |
| **ETL** | Scripts καθαρισμού/μετασχηματισμού raw δεδομένων | Raw data sample + target schema | Python/SQL script | Όχι | Ναι, dry-run πρώτα |
| **Admin tooling** | UI components, workflow forms για admin panel | Wireframe περιγραφή + endpoints | Frontend code | Όχι | Ναι (functional review) |
| **Classification** | Κατηγοριοποίηση venue, εξαγωγή vibe tags από κείμενο | Πηγαίο κείμενο (description/reviews) + λίστα επιτρεπτών tags | **Strict JSON**: `{category, tags:[{tag, confidence, evidence_quote}], summary}` | **Ναι, πάντα** | **Ναι, πάντα πριν publish** |
| **Copywriting** | Venue descriptions, SEO landing page copy, UI microcopy | Facts/data σχετικά με venue ή σελίδα | Κείμενο draft | Όχι | Ναι (tone/factual check) |
| **Test generation** | Unit tests για scoring engine, API endpoints | Function/endpoint code | Test code | Όχι | Ναι (run πριν merge) |
| **Analytics instrumentation** | Ορισμός event schema, tracking code | Event taxonomy (§14) | Code + event spec | Μερικώς (event payload schema) | Ναι |
| **Maintenance** | Debugging, dependency updates, refactors, incident triage | Error log / stack trace | Διάγνωση + fix | Όχι | Ναι, πριν deploy |

**Πότε χρειάζεται strict JSON:** Οτιδήποτε τροφοδοτεί απευθείας τη βάση δεδομένων ή admin queue (classification, tag extraction) — **πάντα** με explicit schema, ώστε το output να είναι parseable και validated πριν αγγίξει DB.

**Πότε χρειάζεται human review:** Οτιδήποτε γίνεται public-facing fact (§8 λίστα), οτιδήποτε αγγίζει production DB, οτιδήποτε αλλάζει architecture.

**Practical recommendation:** Claude ποτέ δεν γράφει απευθείας σε production DB. Πάντα draft/staging state → admin approval → publish.

---

## 10. PROMPTING STRATEGY FOR CLAUDE

### General rules
1. Πάντα δίνε το **τρέχον schema/context**, ποτέ μην υποθέτεις ότι το θυμάται.
2. Για factual/classification tasks: **temperature χαμηλή λογική** (ζήτα "μην κάνεις εικασίες, μόνο ό,τι υποστηρίζεται από το κείμενο").
3. Ζήτα πάντα **confidence field** σε κάθε classification output.
4. Ζήτα πάντα **evidence/source quote** σε κάθε extracted fact.
5. Άγνωστο πεδίο = `null`, ποτέ εικασία-ως-γεγονός.

### Schema-first prompting (template)
```
Context: [περιγραφή domain / σχήμα πίνακα]
Task: Κατηγοριοποίησε το venue παρακάτω βάσει ΜΟΝΟ του δοθέντος κειμένου.
Επιτρεπτές κατηγορίες: [λίστα]
Επιτρεπτά vibe tags: [λίστα]

Venue raw text:
"""
[κείμενο]
"""

Output ΑΥΣΤΗΡΑ σε JSON:
{
  "category": "<μία από τις επιτρεπτές>",
  "tags": [{"tag": "...", "confidence": 0.0-1.0, "evidence_quote": "..."}],
  "summary": "<1 πρόταση, μόνο από το κείμενο>",
  "unknown_fields": ["..."]
}
Αν κάτι δεν υποστηρίζεται από το κείμενο, μην το συμπεριλάβεις.
```

### How to ask for refactors
Δώσε: αρχείο/function πλήρες, τον λόγο refactor (readability/performance/κλπ), τι **δεν** πρέπει να αλλάξει (behavior contract). Ζήτα diff-style output, όχι ολόκληρο rewrite αν η αλλαγή είναι μικρή.

### How to ask for SQL migrations
Δώσε: τρέχον schema (CREATE TABLE των σχετικών πινάκων), το επιθυμητό νέο state, ζήτα **forward migration + rollback**, και ρητά ζήτα να επισημάνει αν η αλλαγή είναι breaking/χρειάζεται backfill.

### How to ask for feature implementation
Δώσε: user story, σχετικά αρχεία/paths, API contract αν υπάρχει, edge cases που ήδη ξέρεις. Ζήτα να ρωτήσει αν κάτι είναι ασαφές αντί να υποθέσει.

### How to ask for bug fixing
Δώσε: ακριβές error/stack trace, βήματα αναπαραγωγής, σχετικό κώδικα (όχι όλο το repo). Ζήτα root cause πρώτα, μετά fix — όχι κατευθείαν patch χωρίς διάγνωση.

### How to ask for structured venue classification
Πάντα με το schema-first template παραπάνω· ποτέ ανοιχτό "πες μου τι νομίζεις ότι είναι αυτό το μαγαζί" χωρίς πηγαίο κείμενο.

### Avoiding hallucinations
- Δώσε πάντα πηγαίο κείμενο, ποτέ "βρες πληροφορίες για το X venue" χωρίς input data
- Ζήτα evidence_quote σε κάθε fact
- Χαμηλό confidence όταν το κείμενο είναι αμφίσημο, ρητά ζητούμενο
- Ποτέ μη δέχεσαι Claude output ως "verified" — είναι πάντα "suggested", state field το επιβεβαιώνει

**Practical recommendation:** Κράτα μια μικρή βιβλιοθήκη prompt templates (markdown files) στο repo (`/prompts/`) ώστε να είναι reusable και versioned, όχι ad-hoc κάθε φορά.

---

## 11. ADMIN PANEL

- **Dashboard**: αριθμός active venues, μέσο confidence, μέγεθος queues (low-confidence/stale/corrections/duplicates), sponsorship status, τελευταία automation runs (✅/❌)
- **Venue review queue**: νέα/pending venues πριν γίνουν active — checklist validation (§8)
- **Low-confidence queue**: venues/tags/hours κάτω από threshold, sorted by "πόσο συχνά εμφανίζονται σε results" (προτεραιότητα σε ό,τι φαίνεται συχνά)
- **Stale data queue**: `last_verified_at` > threshold (π.χ. 60-90 μέρες), sorted by staleness
- **Source verification queue**: sources με failed HTTP check ή reliability_score χαμηλό
- **Sponsor management**: CRUD campaigns, ημερομηνίες, budget, impressions/clicks tracking, expiry alerts
- **Content pages management**: draft/published state, Claude-drafted προτάσεις προς review
- **Analytics snapshots**: ημερήσια/εβδομαδιαία aggregate views (χωρίς να χρειάζεται external BI tool στο MVP)
- **Manual override tools**: force-feature ένα venue, force-hide, manual confidence override με υποχρεωτικό reason field (πάει σε confidence_audits)
- **Logging & audit trail**: κάθε αλλαγή σε venue/tags/hours/confidence καταγράφεται σε `confidence_audits` με who/when/why, προβάλλεται ανά venue σαν timeline

**Practical recommendation:** Οι queues να είναι **saved filtered views** πάνω στους υπάρχοντες πίνακες, όχι ξεχωριστά materialized tables — απλούστερο να συντηρείς solo.

---

## 12. SEO + CONTENT STRATEGY

### Δομή σελίδων
- **Landing ανά περιοχή×intent**: `/thessaloniki/[area]/[intent]` (π.χ. "ήσυχο ποτό στα Λαδάδικα") — δυναμικά παραγόμενη από πραγματικά δεδομένα (top venues στην περιοχή/intent), **όχι** καθαρό AI κείμενο.
- **"Πού να πάω τώρα" pages**: `/pou-na-pao-tora/[intent]` — ζωντανή σελίδα με τα τρέχοντα top αποτελέσματα βάσει ώρας, λειτουργεί σαν "static entry point" προς το ίδιο engine.
- **Evergreen guides**: χειροκίνητα/ημι-αυτόματα curated (π.χ. "Καλύτερα cafe για δουλειά στη Θεσσαλονίκη"), review κάθε few μήνες.
- **Dynamic pages**: αυτο-ανανεώνονται από τη βάση (venue count, top picks) χωρίς να χρειάζονται manual update κάθε φορά.

### Programmatic SEO με guardrails
- **Ελάχιστο threshold δημοσίευσης**: μια area×intent σελίδα δημοσιεύεται **μόνο** αν υπάρχουν ≥6 venues με confidence≥0.6 σε αυτόν τον συνδυασμό — αλλιώς μένει unpublished (αποφυγή thin content).
- Κάθε τέτοια σελίδα περνά από **1 manual spot-check** πριν το πρώτο publish.
- Κανένα page δεν είναι 100% AI-generated παράγραφος· είναι δομημένο block (intro σύντομο + πίνακας/κάρτες πραγματικών venues + confidence-based badges).

### Internal linking
Venue pages ↔ area pages ↔ intent pages ↔ evergreen guides, με contextual, όχι bulk/footer-spam linking.

### Content freshness
`content_pages.last_reviewed_at` + automation surfaces pages που δεν έχουν ανανεωθεί ή που το underlying venue data άλλαξε σημαντικά (νέο venue προστέθηκε στην περιοχή, venue έκλεισε).

### Κανόνες αποφυγής thin content/AI spam
- Καμία σελίδα χωρίς ελάχιστο πραγματικό data volume
- Κανένα mass-generated batch χωρίς δειγματοληπτικό human review
- Κάθε Claude-drafted κείμενο περνά state=draft πριν γίνει published
- Καμία σελίδα-διπλότυπο μόνο με keyword variation χωρίς ουσιαστική διαφορά περιεχομένου

**Practical recommendation:** SEO expansion **μετά** την 4-6η εβδομάδα, αφού το core app έχει ήδη αρκετά verified venues ώστε οι landing pages να έχουν ουσία.

**What to avoid:** Μην τρέξεις programmatic generation πριν υπάρχει data volume — Google penalizes thin/duplicate pattern pages, και θα βλάψει το domain trust πριν καν αποκτήσεις.

---

## 13. MONETIZATION STRATEGY

### Phase 1 (πρώτοι 3-6 μήνες)
- **Display ads** (π.χ. Google AdSense ή τοπικό ad network): μόνο σε σαφώς διαχωρισμένες θέσεις (κάτω από results, sidebar σε desktop), ποτέ interstitial, ποτέ ανάμεσα σε result cards.
- **Category sponsorships**: ένας τοπικός χορηγός ανά vertical (π.χ. μια μπύρα brand χορηγεί το "ήσυχο ποτό" section) — banner label, όχι επιρροή στο ranking score.

### Phase 2 (μετά από traction)
- **Promoted listings**: ξεκάθαρα labeled "Χορηγία" badge, εμφανίζονται σε **ξεχωριστό pinned slot** (π.χ. 1 θέση στην κορυφή μαρκαρισμένη), ποτέ ανακατεμένα αδιάκριτα με organic ranking.
- **Newsletter/local digest sponsorship**: εβδομαδιαίο email "πού να πας αυτό το Σ/Κ" με 1 sponsor slot.
- **Sponsorship packages ανά περιοχή/vertical** με σταθερή τιμολόγηση (μηνιαία), όχι CPC-based, ώστε να μη δημιουργεί κίνητρο για fake clicks.

### Τι να αποφύγεις
- Μην αφήσεις sponsorship να επηρεάζει το relevance score — ξεχωριστό, labeled slot πάντα.
- Μην κάνεις autoplay video ads ή popups/interstitials.
- Μην βάλεις ads πριν αποδειχθεί ότι η core εμπειρία δουλεύει (πρώτα trust).
- Μην βασιστείς σε CPC affiliate μοντέλα που δημιουργούν κίνητρο για τεχνητά clicks (ασύμβατο με τους περιορισμούς σου περί invalid traffic).

### Placement strategy χωρίς ad-heavy αίσθηση
Κανόνας: **ads ≤ 20% του visible viewport** σε κάθε οθόνη, ποτέ πριν το πρώτο result, πάντα μετά από ουσιαστικό content.

**Practical recommendation:** Ξεκίνα με **0 ads** στον πρώτο μήνα — μέτρα πρώτα engagement/trust, ενεργοποίησε ads μετά, ώστε τα πρώτα analytics baseline να μην είναι "μολυσμένα" από ad-induced behavior.

---

## 14. ANALYTICS + KPIs

### Event taxonomy (βασικά properties: session_id, timestamp, + ειδικά ανά event)
| Event | Key properties |
|---|---|
| `search_started` | intent, has_geolocation |
| `filters_applied` | filters(jsonb) |
| `results_viewed` | result_count, relaxed(bool) |
| `venue_clicked` | venue_id, rank_position |
| `directions_clicked` | venue_id, rank_position |
| `save_clicked` | venue_id |
| `feedback_submitted` | venue_id, feedback_type |
| `sponsored_impression` | placement_id, venue_id |
| `sponsored_click` | placement_id, venue_id |
| `stale_data_flagged` | venue_id, field_name |
| `refine_used` | refine_type(quieter/cheaper/closer) |

### KPIs
- **North Star Metric**: **"Επιτυχημένες αποφάσεις"** = search_started που καταλήγει σε venue_clicked ή directions_clicked εντός της ίδιας session.
- **Activation metric**: % πρώτων sessions που φτάνουν σε επιτυχημένη απόφαση εντός <2 λεπτών.
- **Retention indicators**: % sessions που επιστρέφουν εντός 14/30 ημερών και ολοκληρώνουν νέα επιτυχημένη απόφαση.
- **Monetization metrics**: ad viewability rate, CTR, sponsorship fill rate, revenue/1000 sessions.
- **Data quality metrics**: % active venues με overall_confidence≥0.7, % venues stale>90 ημέρες, μέγεθος queues.
- **Trust metrics**: θετικό/αρνητικό feedback ratio, ρυθμός `stale_data_flagged` ανά 1000 impressions (χαμηλό = καλό sign).

**Practical recommendation:** Instrument από μέρα 1, ακόμα κι αν δεν έχεις dashboard ακόμα — τα raw logs είναι το μελλοντικό σου training data για οποιοδήποτε μελλοντικό ML.

---

## 15. AUTOMATION PLAN

| Automation | Συχνότητα | Τι κάνει |
|---|---|---|
| **Daily freshness check** | Καθημερινά (cron) | Εντοπίζει venues με `last_verified_at` > threshold, τα βάζει σε stale queue |
| **Confidence decay** | Καθημερινά | Μειώνει σταδιακά confidence με βάση χρόνο από last_verified_at (π.χ. -0.02/ημέρα μετά τις 30 μέρες) |
| **Recommendation logs processing** | Καθημερινά/batch | Aggregate `recommendation_events`/`search_logs` σε materialized views για dashboard |
| **Broken source detection** | 2x/εβδομάδα | HTTP check σε website/social links στο `venue_sources`, flag αν 404/timeout |
| **Content generation drafts** | Weekly | Claude προτείνει νέα/ανανεωμένα content_pages σε draft state, ποτέ auto-publish |
| **Stale record surfacing** | Καθημερινά | Ενημερώνει admin queue + Telegram summary |
| **Telegram summary για operator** | Καθημερινά | Νέα corrections, νέα duplicates, sponsorship expiring, anomaly flags |
| **Anomaly detection** | Καθημερινά | Ξαφνική πτώση/αύξηση σε search volume ή error rate → alert (πιθανό bug/outage) |
| **Sponsorship expiry alerts** | Καθημερινά | `sponsored_placements.end_date` <7 ημέρες → alert στον operator |

**Practical recommendation:** Ξεκίνα με **APScheduler** μέσα στο ίδιο FastAPI service (simplicity) αντί για ξεχωριστό Celery+Redis cluster — αναβάθμισε σε Celery μόνο όταν ο όγκος jobs το δικαιολογεί. Το Telegram bot ως daily summary είναι πολύ χαμηλού κόστους οπτικό — προτεινόμενο day-1 automation.

**What to avoid:** Μην αυτοματοποιήσεις το publish οποιουδήποτε Claude-generated περιεχομένου/κατηγοριοποίησης — η αυτοματοποίηση αφορά **επισήμανση/προετοιμασία**, όχι τελική δημοσίευση.

---

## 16. TECH STACK RECOMMENDATION

| Layer | Επιλογή | Αιτιολόγηση |
|---|---|---|
| **Backend** | Python + **FastAPI** + Pydantic | Ταιριάζει με προτίμησή σου, type-safe schemas, εύκολο API-first design, καλή Claude-code-generation συμβατότητα |
| **DB** | **PostgreSQL + PostGIS** | Γεωχωρικά queries (ST_DWithin κλπ) απαραίτητα για distance scoring/candidate generation |
| **Task queue / scheduler** | **APScheduler** (MVP) → Celery+Redis (όταν χρειαστεί scale) | Μικρότερη operational πολυπλοκότητα για solo builder αρχικά |
| **Caching** | **Redis** (προαιρετικό MVP, must στο v1.x) | Cache συχνών candidate queries/results ανά περιοχή |
| **Frontend** | **Next.js** (responsive PWA, mobile-first) | Καλό SEO (SSR/ISR για content_pages), όχι native app, ώριμο ecosystem |
| **Maps** | **Leaflet + OpenStreetMap** αρχικά, Mapbox αν χρειαστεί καλύτερο UX/styling αργότερα | Αποφυγή κόστους Google Maps API σε πρώιμο στάδιο· directions deep-link σε Google/Apple Maps εξωτερικά ούτως ή άλλως |
| **Analytics** | **Plausible** ή **PostHog** (self-hostable/privacy-friendly) | Καθαρά first-party events, ευθυγραμμισμένο με "όχι invalid traffic" απαίτηση, όχι βαρύ vendor lock-in |
| **Hosting (backend+DB)** | **Fly.io / Railway** αρχικά (managed Postgres+PostGIS support) | Χαμηλό operational overhead για solo founder, εύκολο scaling up αργότερα |
| **Hosting (frontend)** | **Vercel** | Native Next.js fit, γρήγορο deploy |
| **Auth (admin only)** | Απλό email/password (FastAPI-Users) ή Supabase Auth | Το public app δεν χρειάζεται auth· μόνο το admin panel |
| **Observability** | **Sentry** (errors) + **UptimeRobot** (uptime) | Ελάχιστο operational overhead, αρκετό για solo-maintained σύστημα στο MVP |

**Trade-off:** Next.js προσθέτει κάποια πολυπλοκότητα έναντι ενός καθαρού server-rendered template stack, αλλά αποδίδει σε SEO (καθοριστικό §12) και σε mobile UX polish — δικαιολογημένο investment.

**What to avoid:** Μην ξεκινήσεις με Kubernetes/microservices/multi-region — απόλυτη υπερβολή για MVP ενός solo founder. Monolith FastAPI + Postgres αρκεί για πολύ καιρό.

---

## 17. FOLDER STRUCTURE

```
where-to/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI routers (public + admin)
│   │   │   ├── v1/
│   │   │   │   ├── search.py
│   │   │   │   ├── venues.py
│   │   │   │   ├── feedback.py
│   │   │   │   └── admin/
│   │   ├── core/                 # config, settings, security
│   │   ├── db/
│   │   │   ├── models/           # SQLAlchemy models ανά domain
│   │   │   ├── migrations/       # Alembic
│   │   │   └── session.py
│   │   ├── recommendation/
│   │   │   ├── scoring.py
│   │   │   ├── diversity.py
│   │   │   ├── fallback.py
│   │   │   └── config.py
│   │   ├── ingestion/
│   │   │   ├── seed_loader.py
│   │   │   ├── enrichment/       # Claude-assisted enrichment scripts
│   │   │   ├── duplicate_detection.py
│   │   │   └── validation.py
│   │   ├── automation/           # scheduled jobs
│   │   │   ├── freshness_check.py
│   │   │   ├── confidence_decay.py
│   │   │   ├── telegram_summary.py
│   │   │   └── scheduler.py
│   │   ├── schemas/               # Pydantic request/response
│   │   └── main.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── app/                      # Next.js app router
│   │   ├── (public)/
│   │   │   ├── page.tsx          # home
│   │   │   ├── results/
│   │   │   ├── venue/[slug]/
│   │   │   ├── pou-na-pao-tora/[intent]/
│   │   │   └── thessaloniki/[area]/[intent]/
│   │   └── admin/
│   ├── components/
│   ├── lib/
│   └── package.json
├── prompts/                       # versioned Claude prompt templates
│   ├── classification.md
│   ├── sql_migration.md
│   └── content_draft.md
├── docs/
│   └── where-to/
│       ├── PRODUCT_DESIGN.md      # (αυτό το αρχείο)
│       └── schema.sql
└── infra/
    ├── docker-compose.yml
    └── deploy/
```

**Practical recommendation:** Απλό monorepo (backend+frontend+prompts+docs) — δεν χρειάζεσαι multi-repo complexity σε αυτή την κλίμακα.

---

## 18. 30-DAY EXECUTION PLAN (solo builder + Claude)

### Εβδομάδα 1 — Θεμέλια
- Setup repo, FastAPI+Postgres+PostGIS σε local/dev, βασικό schema (venues, categories, tags, hours, signals, sources, city_areas)
- Alembic migrations
- Ορισμός event taxonomy (χωρίς ακόμα production instrumentation)
- **Deliverable:** Working local DB + API skeleton, seed script framework

### Εβδομάδα 2 — Δεδομένα + Engine
- Χειροκίνητη συλλογή 100-150 venues (2 verticals: ήσυχο ποτό/καφέ + date spots) απευθείας στο admin panel (βασικό CRUD μόνο, όχι polish ακόμα)
- Υλοποίηση deterministic scoring engine + candidate generation (§7)
- Unit tests στο scoring
- **Μετράς:** αριθμός venues με ≥0.7 confidence, coverage ανά περιοχή
- **Deliverable:** `/search` endpoint επιστρέφει ranked results σε πραγματικά δεδομένα

### Εβδομάδα 3 — Frontend core flow
- Next.js: home → filters → results → venue detail → directions (Flow A, §4)
- Mobile-first UI, χωρίς account system
- Βασικό analytics instrumentation (search_started, venue_clicked, directions_clicked)
- **Deliverable:** end-to-end χρηστικό MVP σε staging URL

### Εβδομάδα 4 — Polish, feedback loop, launch prep
- Feedback micro-prompt (thumbs up/down + corrections)
- Βασικό admin queues (low-confidence, stale)
- Telegram daily summary automation
- Soft launch σε μικρό κύκλο (φίλοι/γνωστοί στη Θεσσαλονίκη) πριν public
- **Μετράς:** activation rate, % επιτυχημένων αποφάσεων, feedback ratio
- **Αφήνεις για μετά:** SEO landing pages, sponsorships, "surprise me", saved searches
- **Deliverable:** Minimum Lovable Product — δουλεύει σωστά για 2 verticals, καλύπτει το core wedge persona (ζευγάρι/remote worker) άψογα

**Minimum Lovable Product ορισμός:** Ένας χρήστης στη Θεσσαλονίκη ανοίγει το app, σε <20 δευτερόλεπτα παίρνει 5 προτάσεις για "ήσυχο ποτό τώρα" που είναι όντως ανοιχτές, όντως κοντά, και όντως ήσυχες — και εμπιστεύεται το αποτέλεσμα αρκετά ώστε να πάει directions.

**Practical recommendation:** Μη διαθέσεις καθόλου χρόνο σε SEO/monetization/ML μέσα στις πρώτες 30 μέρες — η πλήρης προτεραιότητα είναι το core loop να είναι αξιόπιστο σε 2 verticals.

---

## 19. RISKS & MITIGATION

| Risk | Mitigation |
|---|---|
| **Data quality risk** (λάθος ωράρια/κλειστά μαγαζιά) | Confidence scoring + source attribution + stale queue + confidence decay· ποτέ auto-trust σε scraped data |
| **Legal / source risk** (χρήση δεδομένων τρίτων, φωτογραφιών) | `license_ok` flag σε media, source attribution υποχρεωτικό, αποφυγή scraping χωρίς άδεια, χρήση επίσημων APIs όπου γίνεται |
| **Stale data risk** | Automated freshness checks + confidence decay + admin queue με SLA |
| **Bad recommendations** (χαμηλή σχετικότητα) | Deterministic, εξηγήσιμο scoring· score_breakdown logging· feedback loop για συνεχή tuning weights |
| **Low retention** | Utility loop βασισμένο σε πραγματική επαναλαμβανόμενη ανάγκη (§1)· "surprise me"/refine buttons αυξάνουν engagement χωρίς να απαιτούν account |
| **Ad overload** | Placement guardrails (§13), 0 ads στον πρώτο μήνα, ≤20% viewport κανόνας |
| **Operational complexity** (solo maintainer) | Automation-first design (§15), simple stack (§16), admin queues αντί manual τρεξίματα, Telegram alerts αντί για συνεχή polling |
| **Hallucination risk from LLM** | Strict JSON + evidence_quote + confidence field σε κάθε classification· Claude output πάντα draft state, ποτέ direct-to-production |
| **Duplicate/incorrect venue entries** | Automated duplicate detection (trigram + geo proximity) + admin review πριν merge |
| **Sponsorship δίνει την εντύπωση bias** | Ξεκάθαρο "Χορηγία" labeling, ranking score ανεπηρέαστο, ξεχωριστό pinned slot |
| **SEO penalty από thin/programmatic content** | Minimum data threshold πριν publish κάθε page-τύπο, manual spot-check πρώτο publish (§12) |

---

## 20. DELIVERABLES

### A. Concise product summary
Το **Where to?** είναι ένα mobile-first, context-aware decision engine για τη Θεσσαλονίκη που απαντά στο ερώτημα "πού να πάω τώρα;" με 3-10 ranked, εξηγήσιμες προτάσεις βασισμένες σε deterministic scoring (intent, απόσταση, ωράριο, budget, vibe, confidence). Ξεκινά από 2 verticals (ήσυχο ποτό/καφέ, date spots), τρέχει σε FastAPI+PostgreSQL/PostGIS+Next.js, χτίζεται με curated + Claude-assisted (human-reviewed) δεδομένα, και μονετοποιείται μέσω labeled ads/sponsorships χωρίς να διακυβεύει το relevance του engine.

### B. Technical blueprint
```
Next.js (mobile-first PWA)
   │  REST calls
   ▼
FastAPI (API-first)
   ├── /search        → recommendation engine (§7)
   ├── /venues/{slug}  → venue detail
   ├── /feedback       → user_feedback
   └── /admin/*        → admin CRUD + queues
   │
   ▼
PostgreSQL + PostGIS
   ├── venues, categories, tags, hours, signals, sources
   ├── search_logs, recommendation_events, user_feedback
   ├── confidence_audits, update_jobs
   └── sponsored_placements, content_pages

APScheduler (in-process)
   ├── daily freshness check
   ├── confidence decay
   ├── Telegram summary
   └── broken source detection

Claude (assisted, όχι source of truth)
   ├── classification drafts → review queue
   ├── content drafts → content_pages(draft)
   └── code/SQL/test generation (dev-time, όχι runtime)
```

### C. Πρώτο SQL schema draft
Αναλυτικό αρχείο: `docs/where-to/schema.sql` (δημιουργείται παράλληλα με αυτό το document).

### D. Πρώτο recommendation pseudo-code
Βλ. §7 — πλήρες pseudo-code `get_recommendations()` / `compute_score()`.

### E. Πρώτο admin workflow draft
```
1. Νέο venue εισάγεται (manual ή Claude-assisted draft)
   status = "pending"
2. Validation check (geom, category, ≥1 source, hours ή "άγνωστο")
   αν αποτύχει → παραμένει σε "venue review queue"
3. Admin εγκρίνει → status = "active", overall_confidence υπολογίζεται
4. Venue εμφανίζεται σε αναζητήσεις
5. Automation: daily freshness check
   αν last_verified_at > 60 ημέρες → μπαίνει σε "stale queue"
6. Feedback/corrections συσσωρεύονται
   αν αρνητικό feedback > threshold → μπαίνει σε "low-confidence queue"
7. Admin re-verify → νέο source, confidence reset, log σε confidence_audits
8. (Παράλληλα) duplicate detection job flag πιθανά duplicates → admin merge/reject
```

### F. Πρώτο backlog 20 εργασιών (implementation order)
1. Setup repo (backend+frontend skeleton, docker-compose local Postgres+PostGIS)
2. Core schema migration: venues, categories, tags, city_areas
3. Core schema migration: venue_hours, venue_signals, venue_sources
4. Core schema migration: search_logs, recommendation_events, user_feedback, confidence_audits
5. Seed loader script (CSV/manual entry → DB)
6. Admin panel: βασικό venue CRUD (χωρίς auth polish ακόμα)
7. Manual seeding: 50 venues πρώτου vertical (ήσυχο ποτό/καφέ)
8. Manual seeding: 50 venues δεύτερου vertical (date spots)
9. Candidate generation query (PostGIS ST_DWithin + hard filters)
10. Scoring engine: intent/distance/open_now/budget/vibe functions
11. Diversity re-ranking + fallback relaxation logic
12. `/search` API endpoint + unit tests
13. `/venues/{slug}` API endpoint
14. Frontend: home page + filters flow
15. Frontend: results page (κάρτες + score breakdown UI)
16. Frontend: venue detail page + directions deep link
17. Feedback micro-prompt (frontend + `/feedback` endpoint)
18. Analytics instrumentation (event taxonomy §14)
19. Automation: daily freshness check + confidence decay + Telegram summary
20. Soft launch σε μικρό κύκλο χρηστών + βασικές admin queues (low-confidence, stale)

**Practical recommendation:** Ακολούθησε αυτή τη σειρά αυστηρά — μην ξεκινήσεις frontend polish (14-16) πριν το scoring engine (9-11) δουλεύει σε πραγματικά δεδομένα, αλλιώς χτίζεις UI πάνω σε άγνωστη ποιότητα δεδομένων/λογικής.
