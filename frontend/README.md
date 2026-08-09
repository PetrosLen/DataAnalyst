# Where to? — Frontend

Next.js (App Router, TypeScript, Tailwind) mobile-first web app. Βλ. `docs/where-to/PRODUCT_DESIGN.md`
για το πλήρες product/technical design.

Υλοποιεί το core user flow (§4, Flow A + Flow D): **Home → filters → results → venue detail →
directions → feedback**, πάνω στο πραγματικό `/search`, `/venues/{slug}`, `/feedback` API του
backend — καμία fake/mock data. Επίσης ένα λειτουργικό admin panel (`/admin`).

## Local setup

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL -> backend URL
npm run dev
```

Χρειάζεται το backend (`../backend`) να τρέχει και να επιτρέπει CORS από το origin του frontend
(`CORS_ORIGINS` στο backend `.env` — βλ. `../backend/README.md`).

## Pages

- `/` — Πρώτη επίσκεψη: "Ποιο σου ταιριάζει;" (Άντρας/Γυναίκα/Άλλο, με ρητή διαφάνεια στο σκοπό —
  βλ. §Gender theme παρακάτω), αποθηκεύεται στο `localStorage`. Μετά: Home filters — επιλογή intent
  (bar/cafe/restaurant/wine_bar), μετακίνηση, budget, "θέλω κάτι ήσυχο" toggle, "Άλλαξε προφίλ
  χρωμάτων" link. Ζητά geolocation, με fallback σε default τοποθεσία (Πλατεία Αριστοτέλους) αν
  αρνηθεί ο χρήστης ή δεν υποστηρίζεται.
- `/results` — Καλεί `POST /search`, δείχνει ranked κάρτες με score/distance/open-now/budget/
  confidence, "Δες γιατί προτάθηκε" (score breakdown), refine buttons ("πιο ήσυχα" → προσθέτει
  tag `quiet` και ξανακάνει search· "πιο οικονομικά" → μειώνει το budget cap· "πιο κοντινά" →
  client-side re-sort, χωρίς νέο API call).
- `/venue/[slug]` — Server component, καλεί `GET /venues/{slug}`, δείχνει hero photo (αν υπάρχει
  εγκεκριμένη — αλλιώς playful placeholder· με caption attribution πάνω στη φωτογραφία όταν το
  API το επιστρέφει, π.χ. φωτογραφίες από Google Places — βλ. backend README §Photos), στοιχεία
  venue + κουμπί "Οδηγίες" (deep link σε Google Maps βάσει διεύθυνσης) + `FeedbackWidget` (👍/👎 +
  "κάτι δεν είναι σωστό" → έκλεισε/λάθος στοιχεία, καλεί `POST /feedback`).
- `/admin` — Login (HTTP Basic credentials, αποθηκευμένα σε `sessionStorage`, όχι localStorage) +
  banner Google Places API usage (`X / 1000 κλήσεις αυτόν τον μήνα`, βλ. backend README §"Monthly
  call cap" — ήρεμο χρώμα κάτω από 75%, κίτρινο πάνω από αυτό, κόκκινο όταν το script έχει
  σταματήσει μόνο του) + venue review queue με tabs ανά status, inline edit ανά venue (όλα τα πεδία
  + tags/sources/photos για context) και κουμπί "Έγκριση τώρα". Κάθε φωτογραφία δείχνει ξεχωριστό
  status "⚠ Χρειάζεται επιβεβαίωση άδειας" / "✓ Εγκεκριμένη άδεια" με δικό της toggle (+ attribution
  caption από κάτω όταν υπάρχει) — μια φωτογραφία **δεν** γίνεται ποτέ public μόνη της απλά επειδή
  προστέθηκε στη βάση. Κάθε tag pill έχει τώρα δικό του "✕" για αφαίρεση, + ένα picker από κάτω
  ("+ Προσθήκη tag…" dropdown με confidence input) για να προσθέσεις οποιοδήποτε tag από το
  dictionary — και ένα πλήρες εβδομαδιαίο ωράριο (Δευ-Κυρ, ώρα ανοίγματος/κλεισίματος + checkbox
  "κλειστό" ανά μέρα, "Αποθήκευση ωραρίου") — και τα δύο ήταν μέχρι πρότινος μόνο μέσω SQL, βλ.
  backend README §"Tag & hours editing". Χρειάζεται admin user (βλ. backend README,
  `create_admin_user` script).

## Σημαντικό: μόνο `status="active"` venues εμφανίζονται στο public app

Τα seeded venues είναι όλα `status="pending"` (βλ. backend README) — το `/results` θα δείξει
"δεν βρέθηκε τίποτα" μέχρι να εγκριθούν κάποια. Έγκριση γίνεται πλέον κανονικά μέσω `/admin`
(login → tab "pending" → expand venue → "Έγκριση τώρα"). Για γρήγορο τοπικό testing χωρίς login,
εναλλακτικά με SQL:

```sql
UPDATE venues SET status='active' WHERE slug IN ('vogatsikou-3', 'thermaikos-bar', 'white-rabbit');
```

## Verification

Ελέγχθηκε: `npm run lint` και `npm run build` (production build, TypeScript strict) καθαρά για
κάθε feature, και πλήρη e2e περάσματα σε πραγματικό Chromium πάνω σε production build
(`next start`, όχι `next dev` — το Turbopack dev-mode HMR websocket δεν λειτουργεί σε αυτό το
sandboxed δίκτυο και μπλοκάρει το React hydration, οπότε το testing έγινε σε production build· σε
κανονικό dev περιβάλλον το `npm run dev` δουλεύει κανονικά):
- Golden path: Home → submit → real `/search` results → expand score breakdown → venue detail →
  directions link
- Admin: λάθος password → error, σωστό login → 10 pending venues, "Έγκριση τώρα" → μετακινείται
  στο tab "active", και επιβεβαιώθηκε ότι εμφανίζεται μετά στο πραγματικό `/search`
- Feedback: venue detail → click "👍 Ναι" → "Ευχαριστούμε" confirmation, επιβεβαιώθηκε η εγγραφή
  στη βάση και ότι εμφανίζεται στο `feedback_counts` του admin detail
- Photos: venue χωρίς εγκεκριμένη φωτογραφία → placeholder· admin εγκρίνει το license → η ίδια
  σελίδα δείχνει πλέον την πραγματική φωτογραφία (επιβεβαιώθηκε το πραγματικό `<img src>` με σωστό
  URL). Σημείωση: μέσα σε αυτό το sandboxed dev container το headless Chromium του Playwright δεν
  έχει πρόσβαση στο δημόσιο internet χωρίς να περάσει από το proxy εξόδου του container, οπότε το
  screenshot εκεί έδειχνε "σπασμένη εικόνα" — επιβεβαιώθηκε ξεχωριστά με πραγματικό HTTP request
  (browser-like headers) ότι η εικόνα φορτώνει κανονικά (200, image/jpeg, ~118KB). Σε πραγματικό
  browser χρήστη ή production deployment δεν υπάρχει τέτοιος περιορισμός.
- Google Places usage banner: γέμισε το `google_places_usage` directly με SQL (καμία πραγματική
  κλήση στο Google δεν χρειάζεται για να το ελέγξεις) και επιβεβαιώθηκαν οπτικά και τα 3 states —
  12/1000 (ήρεμο μωβ), 760/1000 (κίτρινο, "πλησιάζουμε το όριο"), 975/1000 (κόκκινο, "σταμάτησε
  αυτόματα") — μετά καθαρίστηκε η test-only γραμμή από τη βάση.
- Tag & hours editing: στο Vogatsikou 3 (πραγματικό pending venue) πρόσθεσε το tag "Laptop-friendly"
  από το picker (εμφανίστηκε αμέσως με 👤 admin icon + "✕"), έβαλε ωράριο Παρασκευής (18:00-02:00)
  και σημείωσε Κυριακή κλειστό, "Αποθήκευση ωραρίου" → "Αποθηκεύτηκε το ωράριο." confirmation με τα
  σωστά values να μένουν στα inputs μετά το reload του detail. Μετά καθαρίστηκαν όλες οι test-only
  εγγραφές (venue_tags, venue_hours, confidence_audits) ώστε τα πραγματικά seed venues να μείνουν
  ως είχαν.

## Design

Λευκό background, κείμενο σχεδόν-μαύρο. Χρώματα ορίζονται κεντρικά σε `app/globals.css`
(`--background`, `--foreground`, `--accent`, `--accent-2`, `--muted`, `--border`, `--card`,
`--success`, `--danger`) και εκτίθενται ως Tailwind utilities (`bg-accent`, `text-muted`, κ.λπ.) —
άλλαξε τα εκεί, όχι σκόρπιες τιμές μέσα στα components.

## Gender theme (`lib/genderTheme.ts`)

Στην πρώτη επίσκεψη το app ρωτάει "Ποιο σου ταιριάζει;" (Άντρας/Γυναίκα/Άλλο), με ρητή εξήγηση ότι
χρησιμοποιείται μόνο για χρώματα + ελαφρώς πιο ταιριαστές προτάσεις, ποτέ δεν μοιράζεται. Η επιλογή
μπαίνει σε `localStorage` (`whereto_gender_preference`) και εφαρμόζεται ως `<html data-gender="…">`
από το `GenderThemeInit` component (τρέχει σε κάθε σελίδα). Τρεις παλέτες σε `app/globals.css`:

| `data-gender` | accent | accent-2 | Πότε |
|---|---|---|---|
| _(κανένα/"other")_ | μωβ `#7C3AED` | τιρκουάζ `#2DD4BF` | Πριν επιλέξει κανείς· και ρητά αν διαλέξει "Άλλο" |
| `female` | pink `#FF3E7F` | κίτρινο `#FFC93C` | |
| `male` | μπλε `#2563EB` | πορτοκαλί `#FB923C` | |

Το `/admin` (`app/admin/layout.tsx`) **πάντα** μένει στην ουδέτερη παλέτα (`data-gender="other"`
σε wrapper `<div>`), ανεξάρτητα από ό,τι είναι αποθηκευμένο στο ίδιο browser — είναι το εργαλείο
του ιδιοκτήτη, όχι το gendered public app.

Η προτίμηση περνάει και στο backend σε δύο σημεία:
- `preferred_audience` στο `POST /search` (μικρό soft nudge αν το venue είναι ήδη ταγκαρισμένο)
- `audience` στο `POST /feedback` (το `FeedbackWidget` το στέλνει αυτόματα) — αυτό είναι το πιο
  σημαντικό: αρκετά θετικά feedback από το ίδιο δηλωμένο φύλο πάνω σε ένα venue κάνουν το backend
  να ταγκάρει **μόνο του** το venue ως `male-friendly`/`female-friendly`, χωρίς κανείς (ούτε ο
  admin, ούτε το Claude) να το αποφασίσει εκ των προτέρων. Βλ. backend README §"Feedback" για την
  ακριβή λογική (ελάχιστο δείγμα, αναλογία, ποτέ δεν πατάει πάνω σε χειροκίνητο tag admin).
