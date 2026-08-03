"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BUDGET_OPTIONS, DEFAULT_LOCATION, INTENTS, MOBILITY_OPTIONS } from "@/lib/constants";
import type { Mobility } from "@/lib/api";
import {
  clearGenderPreference,
  getStoredGenderPreference,
  storeGenderPreference,
  type GenderPreference,
} from "@/lib/genderTheme";

const GENDER_OPTIONS: { value: GenderPreference; label: string; emoji: string }[] = [
  { value: "male", label: "Άντρας", emoji: "👨" },
  { value: "female", label: "Γυναίκα", emoji: "👩" },
  { value: "other", label: "Άλλο / Προτιμώ να μην πω", emoji: "🌈" },
];

export default function HomePage() {
  const [genderPref, setGenderPref] = useState<GenderPreference | null>(null);
  const [checkedStorage, setCheckedStorage] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time read on mount
    setGenderPref(getStoredGenderPreference());
    setCheckedStorage(true);
  }, []);

  if (!checkedStorage) {
    return <main className="flex-1" />;
  }

  if (!genderPref) {
    return <GenderGate onSelect={setGenderPref} />;
  }

  return <HomeFilters onChangeProfile={() => setGenderPref(null)} />;
}

function GenderGate({ onSelect }: { onSelect: (pref: GenderPreference) => void }) {
  function choose(pref: GenderPreference) {
    storeGenderPreference(pref);
    onSelect(pref);
  }

  return (
    <main className="flex-1 flex flex-col items-center justify-center mx-auto w-full max-w-md px-5 gap-8 text-center">
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight">
          Where to<span className="text-accent">?</span>
        </h1>
        <p className="mt-3 text-foreground font-semibold">Ποιο σου ταιριάζει;</p>
        <p className="mt-1 text-xs text-muted">
          Το χρησιμοποιούμε μόνο για τα χρώματα της εφαρμογής και για λίγο πιο ταιριαστές
          προτάσεις. Ποτέ δεν το μοιραζόμαστε.
        </p>
      </div>

      <div className="w-full flex flex-col gap-3">
        {GENDER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => choose(opt.value)}
            className="w-full rounded-2xl border-2 border-border bg-card px-4 py-4 text-base font-bold text-foreground hover:border-accent hover:text-accent transition-all flex items-center justify-center gap-2"
          >
            <span className="text-xl">{opt.emoji}</span>
            {opt.label}
          </button>
        ))}
      </div>
    </main>
  );
}

function HomeFilters({ onChangeProfile }: { onChangeProfile: () => void }) {
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

  function changeProfile() {
    clearGenderPreference();
    onChangeProfile();
  }

  return (
    <main className="flex-1 flex flex-col mx-auto w-full max-w-md px-5 pt-10 pb-8 gap-8">
      <header className="text-center">
        <span className="inline-block rounded-full bg-accent-2 text-accent-2-foreground text-[11px] font-bold uppercase tracking-wide px-3 py-1 mb-3">
          📍 Θεσσαλονίκη
        </span>
        <h1 className="text-5xl font-extrabold tracking-tight">
          Where to<span className="text-accent">?</span>
        </h1>
        <p className="mt-2 text-muted text-sm">
          Πες μας τι θέλεις τώρα — θα σου δώσουμε κατευθείαν προτάσεις. Χωρίς σκρολάρισμα.
        </p>
      </header>

      <section>
        <h2 className="text-xs font-bold uppercase tracking-wide text-muted mb-3">Τι ψάχνεις</h2>
        <div className="grid grid-cols-2 gap-2">
          {INTENTS.map((opt) => (
            <button
              key={opt.slug}
              type="button"
              onClick={() => setIntent(opt.slug)}
              className={`rounded-2xl px-3 py-3 text-sm font-semibold transition-all border-2 ${
                intent === opt.slug
                  ? "bg-accent text-accent-foreground border-accent shadow-lg shadow-accent/25 scale-[1.02]"
                  : "bg-card border-border text-foreground hover:border-accent/50"
              }`}
            >
              <span className="mr-1.5">{opt.emoji}</span>
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs font-bold uppercase tracking-wide text-muted mb-3">Μετακίνηση</h2>
        <div className="flex gap-2">
          {MOBILITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setMobility(opt.value)}
              className={`flex-1 rounded-2xl px-3 py-2 text-sm font-semibold transition-all border-2 ${
                mobility === opt.value
                  ? "bg-accent text-accent-foreground border-accent shadow-lg shadow-accent/25"
                  : "bg-card border-border text-foreground hover:border-accent/50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs font-bold uppercase tracking-wide text-muted mb-3">
          Budget (μέχρι)
        </h2>
        <div className="flex gap-2">
          {BUDGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setBudgetMax(opt.value)}
              className={`flex-1 rounded-2xl px-3 py-2 text-sm font-semibold transition-all border-2 ${
                budgetMax === opt.value
                  ? "bg-accent-2 text-accent-2-foreground border-accent-2 shadow-lg shadow-accent-2/25"
                  : "bg-card border-border text-foreground hover:border-accent-2/60"
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
          className={`w-full flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-semibold border-2 transition-all ${
            quietOnly ? "bg-accent/10 border-accent text-accent" : "bg-card border-border text-foreground"
          }`}
        >
          <span>🤫 Θέλω κάτι ήσυχο</span>
          <span
            className={`h-6 w-10 rounded-full relative transition-colors ${
              quietOnly ? "bg-accent" : "bg-border"
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
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
        className="mt-2 w-full rounded-full bg-accent text-accent-foreground font-bold py-4 text-base shadow-xl shadow-accent/30 transition-transform active:scale-[0.98] disabled:opacity-60"
      >
        {locating ? "Εντοπισμός τοποθεσίας…" : "Πού να πάω τώρα; →"}
      </button>

      <button
        type="button"
        onClick={changeProfile}
        className="text-xs text-muted hover:text-accent font-medium"
      >
        Άλλαξε προφίλ χρωμάτων
      </button>
    </main>
  );
}
