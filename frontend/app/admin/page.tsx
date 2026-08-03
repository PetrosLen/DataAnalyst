"use client";

import { useEffect, useState } from "react";
import {
  AdminAuthError,
  getVenue,
  listVenues,
  updateVenue,
  verifyCredentials,
  type AdminVenueDetail,
  type AdminVenueListItem,
  type AdminVenueUpdate,
} from "@/lib/adminApi";
import {
  clearCredentials,
  getStoredCredentials,
  storeCredentials,
  type AdminCredentials,
} from "@/lib/adminAuth";

const STATUS_TABS = ["pending", "active", "inactive", "unverified", "merged"] as const;

export default function AdminPage() {
  const [creds, setCreds] = useState<AdminCredentials | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    const stored = getStoredCredentials();
    if (!stored) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time session check on mount
      setCheckingSession(false);
      return;
    }
    verifyCredentials(stored)
      .then((ok) => {
        if (ok) setCreds(stored);
        else clearCredentials();
      })
      .finally(() => setCheckingSession(false));
  }, []);

  if (checkingSession) {
    return <Centered>Έλεγχος σύνδεσης…</Centered>;
  }

  if (!creds) {
    return <LoginForm onSuccess={setCreds} />;
  }

  return (
    <VenueReviewQueue
      creds={creds}
      onLogout={() => {
        clearCredentials();
        setCreds(null);
      }}
    />
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex-1 flex items-center justify-center text-neutral-400 text-sm">
      {children}
    </main>
  );
}

function LoginForm({ onSuccess }: { onSuccess: (creds: AdminCredentials) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const creds = { email, password };
    const ok = await verifyCredentials(creds).catch(() => false);
    setLoading(false);
    if (!ok) {
      setError("Λάθος email ή password.");
      return;
    }
    storeCredentials(creds);
    onSuccess(creds);
  }

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-5">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-xs flex flex-col gap-3 rounded-2xl border border-neutral-800 bg-neutral-900 p-6"
      >
        <h1 className="text-lg font-semibold text-center mb-2">Where to? Admin</h1>
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg bg-neutral-950 border border-neutral-700 px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <input
          type="password"
          required
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-lg bg-neutral-950 border border-neutral-700 px-3 py-2 text-sm outline-none focus:border-accent"
        />
        {error && <p className="text-xs text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-accent text-neutral-950 font-semibold py-2 text-sm disabled:opacity-60"
        >
          {loading ? "…" : "Σύνδεση"}
        </button>
      </form>
    </main>
  );
}

function VenueReviewQueue({
  creds,
  onLogout,
}: {
  creds: AdminCredentials;
  onLogout: () => void;
}) {
  const [status, setStatus] = useState<string>("pending");
  const [venues, setVenues] = useState<AdminVenueListItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const res = await listVenues(creds, status);
      setVenues(res.items);
      setTotal(res.total);
    } catch (err) {
      if (err instanceof AdminAuthError) {
        onLogout();
        return;
      }
      setError("Αποτυχία φόρτωσης.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- refetch on status tab change is intentional
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  return (
    <main className="flex-1 flex flex-col mx-auto w-full max-w-2xl px-5 pt-6 pb-10 gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Venue review queue</h1>
        <button
          type="button"
          onClick={onLogout}
          className="text-xs text-neutral-400 hover:text-neutral-200"
        >
          Αποσύνδεση ({creds.email})
        </button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setStatus(tab)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium border ${
              status === tab
                ? "bg-accent text-neutral-950 border-accent"
                : "border-neutral-700 text-neutral-300"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {loading && <p className="text-neutral-400 text-sm">Φόρτωση…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {!loading && venues && (
        <p className="text-xs text-neutral-500">{total} venues σε status=&quot;{status}&quot;</p>
      )}

      <ul className="flex flex-col gap-2">
        {venues?.map((v) => (
          <li key={v.id}>
            <VenueRow
              venue={v}
              expanded={selectedId === v.id}
              onToggle={() => setSelectedId(selectedId === v.id ? null : v.id)}
              creds={creds}
              onAuthError={onLogout}
              onSaved={refresh}
            />
          </li>
        ))}
      </ul>
      {!loading && venues && venues.length === 0 && (
        <p className="text-neutral-500 text-sm">Καμία καταχώρηση σε αυτό το status.</p>
      )}
    </main>
  );
}

function VenueRow({
  venue,
  expanded,
  onToggle,
  creds,
  onAuthError,
  onSaved,
}: {
  venue: AdminVenueListItem;
  expanded: boolean;
  onToggle: () => void;
  creds: AdminCredentials;
  onAuthError: () => void;
  onSaved: () => void;
}) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <p className="font-medium text-neutral-100">{venue.name}</p>
          <p className="text-xs text-neutral-500">
            {venue.primary_category_slug ?? "—"} · {venue.city_area_slug ?? "—"} · conf{" "}
            {Math.round(venue.overall_confidence * 100)}%
          </p>
        </div>
        <StatusBadge status={venue.status} />
      </button>
      {expanded && (
        <VenueEditPanel
          venueId={venue.id}
          creds={creds}
          onAuthError={onAuthError}
          onSaved={onSaved}
        />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "active"
      ? "bg-emerald-400/20 text-emerald-400"
      : status === "pending"
        ? "bg-amber-400/20 text-amber-400"
        : "bg-neutral-700 text-neutral-300";
  return <span className={`rounded-full px-2 py-1 text-[10px] font-medium ${color}`}>{status}</span>;
}

function VenueEditPanel({
  venueId,
  creds,
  onAuthError,
  onSaved,
}: {
  venueId: number;
  creds: AdminCredentials;
  onAuthError: () => void;
  onSaved: () => void;
}) {
  const [detail, setDetail] = useState<AdminVenueDetail | null>(null);
  const [form, setForm] = useState<AdminVenueUpdate>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getVenue(creds, venueId)
      .then((d) => {
        if (cancelled) return;
        setDetail(d);
        setForm({
          name: d.name,
          description_short: d.description_short ?? "",
          address: d.address ?? "",
          phone: d.phone ?? "",
          price_level: d.price_level ?? undefined,
          status: d.status,
          overall_confidence: d.overall_confidence,
        });
      })
      .catch((err) => {
        if (err instanceof AdminAuthError) onAuthError();
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [venueId]);

  async function save() {
    setSaving(true);
    setMessage(null);
    try {
      await updateVenue(creds, venueId, form);
      setMessage("Αποθηκεύτηκε.");
      onSaved();
    } catch (err) {
      if (err instanceof AdminAuthError) {
        onAuthError();
        return;
      }
      setMessage("Αποτυχία αποθήκευσης.");
    } finally {
      setSaving(false);
    }
  }

  async function approveNow() {
    setSaving(true);
    setMessage(null);
    try {
      await updateVenue(creds, venueId, { status: "active" });
      setForm((f) => ({ ...f, status: "active" }));
      setMessage("Εγκρίθηκε.");
      onSaved();
    } catch (err) {
      if (err instanceof AdminAuthError) onAuthError();
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="px-4 pb-4 text-xs text-neutral-500">Φόρτωση στοιχείων…</p>;
  }
  if (!detail) {
    return <p className="px-4 pb-4 text-xs text-red-400">Σφάλμα φόρτωσης.</p>;
  }

  return (
    <div className="border-t border-neutral-800 px-4 py-4 flex flex-col gap-3">
      <div className="flex flex-wrap gap-1.5">
        {detail.tags.map((t) => (
          <span
            key={t.slug}
            className="text-[10px] rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-400"
          >
            {t.name} ({Math.round(t.confidence * 100)}%)
          </span>
        ))}
      </div>

      <div className="text-[11px] text-neutral-500 flex flex-col gap-0.5">
        {detail.sources.map((s) => (
          <span key={s.id}>
            πηγή: {s.source_type} · reliability {Math.round(s.reliability_score * 100)}%
          </span>
        ))}
      </div>

      <Field label="Όνομα">
        <input
          value={form.name ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          className="admin-input"
        />
      </Field>
      <Field label="Σύντομη περιγραφή">
        <input
          value={form.description_short ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, description_short: e.target.value }))}
          className="admin-input"
        />
      </Field>
      <Field label="Διεύθυνση">
        <input
          value={form.address ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
          className="admin-input"
        />
      </Field>
      <Field label="Τηλέφωνο">
        <input
          value={form.phone ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
          className="admin-input"
        />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Price level (1-4)">
          <input
            type="number"
            min={1}
            max={4}
            value={form.price_level ?? ""}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                price_level: e.target.value ? Number(e.target.value) : undefined,
              }))
            }
            className="admin-input"
          />
        </Field>
        <Field label="Confidence (0-1)">
          <input
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={form.overall_confidence ?? ""}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                overall_confidence: e.target.value ? Number(e.target.value) : undefined,
              }))
            }
            className="admin-input"
          />
        </Field>
      </div>
      <Field label="Status">
        <select
          value={form.status ?? detail.status}
          onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
          className="admin-input"
        >
          {STATUS_TABS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </Field>

      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="flex-1 rounded-lg bg-accent text-neutral-950 font-semibold py-2 text-sm disabled:opacity-60"
        >
          Αποθήκευση
        </button>
        {detail.status !== "active" && (
          <button
            type="button"
            onClick={approveNow}
            disabled={saving}
            className="flex-1 rounded-lg border border-emerald-400 text-emerald-400 font-semibold py-2 text-sm disabled:opacity-60"
          >
            Έγκριση τώρα
          </button>
        )}
      </div>
      {message && <p className="text-xs text-neutral-400">{message}</p>}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-neutral-400">
      {label}
      {children}
    </label>
  );
}
