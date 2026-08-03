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

- `/` — Home: επιλογή intent (bar/cafe/restaurant/wine_bar), μετακίνηση, budget, "θέλω κάτι ήσυχο"
  toggle. Ζητά geolocation, με fallback σε default τοποθεσία (Πλατεία Αριστοτέλους) αν αρνηθεί ο
  χρήστης ή δεν υποστηρίζεται.
- `/results` — Καλεί `POST /search`, δείχνει ranked κάρτες με score/distance/open-now/budget/
  confidence, "Δες γιατί προτάθηκε" (score breakdown), refine buttons ("πιο ήσυχα" → προσθέτει
  tag `quiet` και ξανακάνει search· "πιο οικονομικά" → μειώνει το budget cap· "πιο κοντινά" →
  client-side re-sort, χωρίς νέο API call).
- `/venue/[slug]` — Server component, καλεί `GET /venues/{slug}`, δείχνει hero photo (αν υπάρχει
  εγκεκριμένη — αλλιώς playful placeholder), στοιχεία venue + κουμπί "Οδηγίες" (deep link σε Google
  Maps βάσει διεύθυνσης) + `FeedbackWidget` (👍/👎 + "κάτι δεν είναι σωστό" → έκλεισε/λάθος
  στοιχεία, καλεί `POST /feedback`).
- `/admin` — Login (HTTP Basic credentials, αποθηκευμένα σε `sessionStorage`, όχι localStorage) +
  venue review queue με tabs ανά status, inline edit ανά venue (όλα τα πεδία + tags/sources/photos
  για context) και κουμπί "Έγκριση τώρα". Κάθε φωτογραφία δείχνει ξεχωριστό status "⚠ Χρειάζεται
  επιβεβαίωση άδειας" / "✓ Εγκεκριμένη άδεια" με δικό της toggle — μια φωτογραφία **δεν** γίνεται
  ποτέ public μόνη της απλά επειδή προστέθηκε στη βάση. Χρειάζεται admin user (βλ. backend README,
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

## Design

Παλέτα: λευκό background, κείμενο σχεδόν-μαύρο, accent hot-pink (`#FF3E7F`) + κίτρινο (`#FFC93C`)
για δεύτερης τάξης highlights/badges. Ορίζεται κεντρικά σε `app/globals.css` (`--background`,
`--foreground`, `--accent`, `--accent-2`, `--muted`, `--border`, `--card`, `--success`, `--danger`)
και εκτίθεται ως Tailwind utilities (`bg-accent`, `text-muted`, κ.λπ.) — άλλαξε τα εκεί, όχι
σκόρπιες τιμές μέσα στα components.
