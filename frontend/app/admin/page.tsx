"use client";

import { useEffect, useState } from "react";
import {
  AdminAuthError,
  getVenue,
  listVenues,
  updateVenue,
  updateVenueMediaLicense,
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
    <main className="flex-1 flex items-center justify-center text-muted text-sm">{children}</main>
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
        className="w-full max-w-xs flex flex-col gap-3 rounded-2xl border border-border bg-card shadow-sm p-6"
      >
        <h1 className="text-lg font-bold text-center mb-2">Where to? Admin</h1>
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="admin-input"
        />
        <input
          type="password"
          required
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="admin-input"
        />
        {error && <p className="text-xs text-danger">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-accent text-accent-foreground font-bold py-2 text-sm disabled:opacity-60"
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
        <h1 className="text-lg font-bold">Venue review queue</h1>
        <button
          type="button"
          onClick={onLogout}
          className="text-xs text-muted hover:text-accent font-medium"
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
            className={`rounded-full px-3 py-1.5 text-xs font-bold border-2 ${
              status === tab
                ? "bg-accent text-accent-foreground border-accent"
                : "border-border bg-card text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {loading && <p className="text-muted text-sm">Φόρτωση…</p>}
      {error && <p className="text-danger text-sm">{error}</p>}
      {!loading && venues && (
        <p className="text-xs text-muted">{total} venues σε status=&quot;{status}&quot;</p>
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
        <p className="text-muted text-sm">Καμία καταχώρηση σε αυτό το status.</p>
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
    <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <p className="font-bold text-foreground">{venue.name}</p>
          <p className="text-xs text-muted">
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
      ? "bg-success/15 text-success"
      : status === "pending"
        ? "bg-accent-2/30 text-accent-2-foreground"
        : "bg-border text-muted";
  return (
    <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${color}`}>{status}</span>
  );
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

  async function toggleMediaLicense(mediaId: number, nextValue: boolean) {
    try {
      const updated = await updateVenueMediaLicense(creds, venueId, mediaId, nextValue);
      setDetail(updated);
    } catch (err) {
      if (err instanceof AdminAuthError) onAuthError();
    }
  }

  if (loading) {
    return <p className="px-4 pb-4 text-xs text-muted">Φόρτωση στοιχείων…</p>;
  }
  if (!detail) {
    return <p className="px-4 pb-4 text-xs text-danger">Σφάλμα φόρτωσης.</p>;
  }

  return (
    <div className="border-t border-border px-4 py-4 flex flex-col gap-3">
      <div className="flex flex-wrap gap-1.5">
        {detail.tags.map((t) => (
          <span
            key={t.slug}
            title={assignedByLabel(t.assigned_by)}
            className="text-[10px] font-medium rounded-full border border-border px-2 py-0.5 text-muted"
          >
            {assignedByIcon(t.assigned_by)} {t.name} ({Math.round(t.confidence * 100)}%)
          </span>
        ))}
      </div>

      <div className="text-[11px] text-muted flex flex-col gap-0.5">
        {detail.sources.map((s) => (
          <span key={s.id}>
            πηγή: {s.source_type} · reliability {Math.round(s.reliability_score * 100)}%
          </span>
        ))}
      </div>

      {detail.media.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold text-muted">
            Φωτογραφίες ({detail.media.length})
          </p>
          <div className="flex flex-col gap-2">
            {detail.media.map((m) => (
              <div key={m.id} className="flex items-center gap-2">
                {/* eslint-disable-next-line @next/next/no-img-element -- external, unpredictable domains */}
                <img
                  src={m.url}
                  alt=""
                  className="h-14 w-14 rounded-xl object-cover border border-border shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] text-muted truncate">{m.url}</p>
                  <p
                    className={`text-[10px] font-bold ${m.license_ok ? "text-success" : "text-danger"}`}
                  >
                    {m.license_ok ? "✓ Εγκεκριμένη άδεια" : "⚠ Χρειάζεται επιβεβαίωση άδειας"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => toggleMediaLicense(m.id, !m.license_ok)}
                  className={`shrink-0 text-[10px] font-bold rounded-full border-2 px-2.5 py-1 ${
                    m.license_ok
                      ? "border-border text-muted"
                      : "border-success text-success"
                  }`}
                >
                  {m.license_ok ? "Απόκρυψη" : "Έγκριση"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

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
          className="flex-1 rounded-full bg-accent text-accent-foreground font-bold py-2 text-sm disabled:opacity-60"
        >
          Αποθήκευση
        </button>
        {detail.status !== "active" && (
          <button
            type="button"
            onClick={approveNow}
            disabled={saving}
            className="flex-1 rounded-full border-2 border-success text-success font-bold py-2 text-sm disabled:opacity-60"
          >
            Έγκριση τώρα
          </button>
        )}
      </div>
      {message && <p className="text-xs text-muted">{message}</p>}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-muted">
      {label}
      {children}
    </label>
  );
}

function assignedByIcon(assignedBy: string): string {
  if (assignedBy === "admin") return "👤";
  if (assignedBy === "claude_suggested") return "✨";
  if (assignedBy === "user_feedback") return "📊";
  return "•";
}

function assignedByLabel(assignedBy: string): string {
  if (assignedBy === "admin") return "Χειροκίνητα από admin";
  if (assignedBy === "claude_suggested") return "Πρόταση Claude — χρειάζεται review";
  if (assignedBy === "user_feedback") return "Προέκυψε από πραγματικό feedback χρηστών";
  return assignedBy;
}
