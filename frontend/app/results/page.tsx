"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ApiError, search, type Mobility, type VenueRecommendation } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { INTENTS } from "@/lib/constants";

const OPEN_STATUS_LABEL: Record<string, string> = {
  open: "Ανοιχτό τώρα",
  closed: "Κλειστό τώρα",
  unknown: "Άγνωστο ωράριο",
};

const OPEN_STATUS_COLOR: Record<string, string> = {
  open: "text-emerald-400",
  closed: "text-red-400",
  unknown: "text-neutral-500",
};

function priceLabel(level: number | null): string {
  if (!level) return "—";
  return "€".repeat(level);
}

export default function ResultsPage() {
  return (
    <Suspense
      fallback={<p className="text-neutral-400 text-sm py-8 text-center">Φόρτωση…</p>}
    >
      <ResultsContent />
    </Suspense>
  );
}

function ResultsContent() {
  const searchParams = useSearchParams();

  const intent = searchParams.get("intent") ?? INTENTS[0].slug;
  const mobility = (searchParams.get("mobility") as Mobility) ?? "walk";
  const lat = Number(searchParams.get("lat"));
  const lon = Number(searchParams.get("lon"));
  const budgetMaxParam = searchParams.get("budget_max");
  const tagsParam = searchParams.get("tags");

  const [budgetMax, setBudgetMax] = useState<number | null>(
    budgetMaxParam ? Number(budgetMaxParam) : null
  );
  const [tags, setTags] = useState<string[]>(tagsParam ? tagsParam.split(",") : []);
  const [sortByDistance, setSortByDistance] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const [results, setResults] = useState<VenueRecommendation[] | null>(null);
  const [relaxed, setRelaxed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const intentLabel = INTENTS.find((i) => i.slug === intent)?.label ?? intent;
  const hasValidLocation = !Number.isNaN(lat) && !Number.isNaN(lon);

  useEffect(() => {
    if (!hasValidLocation) return;
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- resetting loading/error at the start of each new search is intentional
    setLoading(true);
    setError(null);
    search({
      session_id: getSessionId(),
      lat,
      lon,
      intent_category_slug: intent,
      mobility,
      budget_max_level: budgetMax,
      preferred_tag_slugs: tags,
    })
      .then((res) => {
        if (cancelled) return;
        setResults(res.results);
        setRelaxed(res.relaxed);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setError("Άγνωστη κατηγορία αναζήτησης.");
        } else {
          setError("Κάτι πήγε στραβά. Δοκίμασε ξανά.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intent, mobility, lat, lon, budgetMax, tags.join(",")]);

  const displayedResults = useMemo(() => {
    if (!results) return null;
    if (!sortByDistance) return results;
    return [...results].sort((a, b) => a.distance_km - b.distance_km);
  }, [results, sortByDistance]);

  const effectiveError = !hasValidLocation
    ? "Λείπει η τοποθεσία. Γύρνα στην αρχική σελίδα."
    : error;
  const effectiveLoading = hasValidLocation && loading;

  function toggleExpanded(slug: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  function makeQuieter() {
    if (!tags.includes("quiet")) setTags((t) => [...t, "quiet"]);
  }

  function makeCheaper() {
    setBudgetMax((b) => Math.max(1, (b ?? 4) - 1));
  }

  return (
    <main className="flex-1 flex flex-col mx-auto w-full max-w-md px-5 pt-6 pb-10 gap-4">
      <div className="flex items-center justify-between">
        <Link href="/" className="text-sm text-neutral-400 hover:text-neutral-200">
          ← Πίσω
        </Link>
        <h1 className="text-sm font-medium text-neutral-300">{intentLabel}</h1>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <button
          type="button"
          onClick={makeQuieter}
          className="rounded-full border border-neutral-700 px-3 py-1.5 text-neutral-300 hover:border-accent hover:text-accent"
        >
          Δείξε πιο ήσυχα
        </button>
        <button
          type="button"
          onClick={makeCheaper}
          className="rounded-full border border-neutral-700 px-3 py-1.5 text-neutral-300 hover:border-accent hover:text-accent"
        >
          Δείξε πιο οικονομικά
        </button>
        <button
          type="button"
          onClick={() => setSortByDistance((v) => !v)}
          className={`rounded-full border px-3 py-1.5 ${
            sortByDistance
              ? "border-accent text-accent"
              : "border-neutral-700 text-neutral-300 hover:border-accent hover:text-accent"
          }`}
        >
          Δείξε πιο κοντινά
        </button>
      </div>

      {relaxed && !effectiveLoading && (
        <p className="text-xs text-amber-400/80 bg-amber-400/10 rounded-lg px-3 py-2">
          Λίγα αποτελέσματα βρέθηκαν — διευρύναμε την αναζήτηση.
        </p>
      )}

      {effectiveLoading && (
        <p className="text-neutral-400 text-sm py-8 text-center">Ψάχνουμε…</p>
      )}

      {effectiveError && !effectiveLoading && (
        <p className="text-red-400 text-sm py-8 text-center">{effectiveError}</p>
      )}

      {!effectiveLoading && !effectiveError && displayedResults && displayedResults.length === 0 && (
        <p className="text-neutral-400 text-sm py-8 text-center">
          Δεν βρέθηκε τίποτα κοντά σου αυτή τη στιγμή.
        </p>
      )}

      <ul className="flex flex-col gap-3">
        {displayedResults?.map((venue, idx) => (
          <li
            key={venue.slug}
            className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4 flex flex-col gap-2"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <Link
                  href={`/venue/${venue.slug}`}
                  className="font-semibold text-neutral-50 hover:text-accent"
                >
                  {idx + 1}. {venue.name}
                </Link>
                {venue.description_short && (
                  <p className="text-xs text-neutral-400 mt-0.5">{venue.description_short}</p>
                )}
              </div>
              <span className="shrink-0 text-xs font-mono rounded-full bg-neutral-800 px-2 py-1 text-accent">
                {Math.round(venue.score * 100)}
              </span>
            </div>

            <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-neutral-400">
              <span>{venue.distance_km} km</span>
              <span className={OPEN_STATUS_COLOR[venue.open_status]}>
                {OPEN_STATUS_LABEL[venue.open_status]}
              </span>
              <span>{priceLabel(venue.price_level)}</span>
              <span title="Confidence δεδομένων">
                Confidence: {Math.round(venue.overall_confidence * 100)}%
              </span>
            </div>

            <div className="flex gap-2 pt-1">
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${venue.name}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-medium rounded-lg bg-accent text-neutral-950 px-3 py-1.5"
              >
                Οδηγίες
              </a>
              <button
                type="button"
                onClick={() => toggleExpanded(venue.slug)}
                className="text-xs font-medium rounded-lg border border-neutral-700 px-3 py-1.5 text-neutral-300"
              >
                Δες γιατί προτάθηκε
              </button>
            </div>

            {expanded.has(venue.slug) && (
              <dl className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-neutral-400 border-t border-neutral-800 pt-2">
                <ScoreRow label="Ταίριασμα intent" value={venue.score_breakdown.intent} />
                <ScoreRow label="Απόσταση" value={venue.score_breakdown.distance} />
                <ScoreRow label="Ανοιχτό τώρα" value={venue.score_breakdown.open_now} />
                <ScoreRow label="Budget fit" value={venue.score_breakdown.budget} />
                <ScoreRow label="Vibe match" value={venue.score_breakdown.vibe} />
                <ScoreRow
                  label="Confidence δεδομένων"
                  value={venue.score_breakdown.confidence_multiplier}
                />
              </dl>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <>
      <dt>{label}</dt>
      <dd className="text-right text-neutral-300">{Math.round(value * 100)}%</dd>
    </>
  );
}
