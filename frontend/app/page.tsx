"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BUDGET_OPTIONS, DEFAULT_LOCATION, INTENTS, MOBILITY_OPTIONS } from "@/lib/constants";
import type { Mobility } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [intent, setIntent] = useState<string>(INTENTS[0].slug);
  const [mobility, setMobility] = useState<Mobility>("walk");
  const [budgetMax, setBudgetMax] = useState<number>(3);
  const [quietOnly, setQuietOnly] = useState(false);
  const [locating, setLocating] = useState(false);

  function goToResults(lat: number, lon: number) {
    const params = new URLSearchParams({
      intent,
      mobility,
      budget_max: String(budgetMax),
      lat: String(lat),
      lon: String(lon),
    });
    if (quietOnly) params.set("tags", "quiet");
    router.push(`/results?${params.toString()}`);
  }

  function handleSubmit() {
    if (!navigator.geolocation) {
      goToResults(DEFAULT_LOCATION.lat, DEFAULT_LOCATION.lon);
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        goToResults(pos.coords.latitude, pos.coords.longitude);
      },
      () => {
        setLocating(false);
        goToResults(DEFAULT_LOCATION.lat, DEFAULT_LOCATION.lon);
      },
      { timeout: 5000 }
    );
  }

  return (
    <main className="flex-1 flex flex-col mx-auto w-full max-w-md px-5 pt-10 pb-8 gap-8">
      <header className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Where to<span className="text-accent">?</span>
        </h1>
        <p className="mt-2 text-neutral-400 text-sm">
          Πες μας τι θέλεις τώρα στη Θεσσαλονίκη — θα σου δώσουμε κατευθείαν προτάσεις.
        </p>
      </header>

      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-3">
          Τι ψάχνεις
        </h2>
        <div className="grid grid-cols-2 gap-2">
          {INTENTS.map((opt) => (
            <button
              key={opt.slug}
              type="button"
              onClick={() => setIntent(opt.slug)}
              className={`rounded-xl px-3 py-3 text-sm font-medium transition-colors border ${
                intent === opt.slug
                  ? "bg-accent text-neutral-950 border-accent"
                  : "bg-neutral-900 border-neutral-800 text-neutral-200 hover:border-neutral-600"
              }`}
            >
              <span className="mr-1.5">{opt.emoji}</span>
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-3">
          Μετακίνηση
        </h2>
        <div className="flex gap-2">
          {MOBILITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setMobility(opt.value)}
              className={`flex-1 rounded-xl px-3 py-2 text-sm font-medium transition-colors border ${
                mobility === opt.value
                  ? "bg-accent text-neutral-950 border-accent"
                  : "bg-neutral-900 border-neutral-800 text-neutral-200 hover:border-neutral-600"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-3">
          Budget (μέχρι)
        </h2>
        <div className="flex gap-2">
          {BUDGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setBudgetMax(opt.value)}
              className={`flex-1 rounded-xl px-3 py-2 text-sm font-medium transition-colors border ${
                budgetMax === opt.value
                  ? "bg-accent text-neutral-950 border-accent"
                  : "bg-neutral-900 border-neutral-800 text-neutral-200 hover:border-neutral-600"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <button
          type="button"
          onClick={() => setQuietOnly((v) => !v)}
          className={`w-full flex items-center justify-between rounded-xl px-4 py-3 text-sm font-medium border transition-colors ${
            quietOnly
              ? "bg-accent/10 border-accent text-accent"
              : "bg-neutral-900 border-neutral-800 text-neutral-300"
          }`}
        >
          <span>Θέλω κάτι ήσυχο</span>
          <span
            className={`h-5 w-9 rounded-full relative transition-colors ${
              quietOnly ? "bg-accent" : "bg-neutral-700"
            }`}
          >
            <span
              className={`absolute top-0.5 h-4 w-4 rounded-full bg-neutral-950 transition-transform ${
                quietOnly ? "translate-x-4" : "translate-x-0.5"
              }`}
            />
          </span>
        </button>
      </section>

      <button
        type="button"
        onClick={handleSubmit}
        disabled={locating}
        className="mt-2 w-full rounded-2xl bg-accent text-neutral-950 font-semibold py-4 text-base disabled:opacity-60"
      >
        {locating ? "Εντοπισμός τοποθεσίας…" : "Πού να πάω τώρα;"}
      </button>
    </main>
  );
}
