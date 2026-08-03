# Where to? — Frontend

Next.js (App Router, TypeScript, Tailwind) mobile-first web app. Βλ. `docs/where-to/PRODUCT_DESIGN.md`
για το πλήρες product/technical design.

Υλοποιεί το core user flow (§4, Flow A): **Home → filters → results → venue detail → directions**,
πάνω στο πραγματικό `/search` και `/venues/{slug}` API του backend — καμία fake/mock data.

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

- `/` — Home: επιλογή intent (bar/cafe/restaurant/wine_bar), μετακίνηση, budget, "θέλω κάτι ήσυχο"
  toggle. Ζητά geolocation, με fallback σε default τοποθεσία (Πλατεία Αριστοτέλους) αν αρνηθεί ο
  χρήστης ή δεν υποστηρίζεται.
- `/results` — Καλεί `POST /search`, δείχνει ranked κάρτες με score/distance/open-now/budget/
  confidence, "Δες γιατί προτάθηκε" (score breakdown), refine buttons ("πιο ήσυχα" → προσθέτει
  tag `quiet` και ξανακάνει search· "πιο οικονομικά" → μειώνει το budget cap· "πιο κοντινά" →
  client-side re-sort, χωρίς νέο API call).
- `/venue/[slug]` — Server component, καλεί `GET /venues/{slug}`, δείχνει στοιχεία venue + κουμπί
  "Οδηγίες" (deep link σε Google Maps βάσει διεύθυνσης).

## Σημαντικό: μόνο `status="active"` venues εμφανίζονται

Τα seeded venues είναι όλα `status="pending"` (βλ. backend README) — το `/results` θα δείξει
"δεν βρέθηκε τίποτα" μέχρι να εγκριθούν κάποια. Για τοπικό development/testing, ενεργοποίησέ τα
προσωρινά απευθείας στη βάση (δεν υπάρχει ακόμα admin UI):

```sql
UPDATE venues SET status='active' WHERE slug IN ('vogatsikou-3', 'thermaikos-bar', 'white-rabbit');
```

## Verification

Ελέγχθηκε: `npm run lint` και `npm run build` (production build, TypeScript strict) καθαρά, και
πλήρες golden-path e2e πέρασμα σε πραγματικό Chromium (Home → submit → real `/search` results →
expand score breakdown → venue detail → directions link) πάνω σε production build (`next start`) —
όχι `next dev`, γιατί το Turbopack dev-mode HMR websocket δεν λειτουργεί σε αυτό το sandboxed
δίκτυο και μπλοκάρει το React hydration· σε κανονικό dev περιβάλλον το `npm run dev` δουλεύει
κανονικά.
