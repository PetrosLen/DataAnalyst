"use client";

import { useState } from "react";
import { submitFeedback, type FeedbackType } from "@/lib/api";
import { getSessionId } from "@/lib/session";
import { getStoredGenderPreference } from "@/lib/genderTheme";

export default function FeedbackWidget({ venueSlug }: { venueSlug: string }) {
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [showCorrection, setShowCorrection] = useState(false);

  async function send(feedbackType: FeedbackType) {
    setStatus("sending");
    try {
      await submitFeedback({
        sessionId: getSessionId(),
        venueSlug,
        feedbackType,
        audience: getStoredGenderPreference() ?? "other",
      });
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") {
    return (
      <div className="rounded-2xl border border-border bg-card px-4 py-3 text-sm text-foreground font-medium">
        Ευχαριστούμε για το feedback! 🙌
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-card px-4 py-3 flex flex-col gap-2">
      <p className="text-sm font-semibold text-foreground">Ήταν καλή πρόταση;</p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => send("thumbs_up")}
          disabled={status === "sending"}
          className="flex-1 rounded-full border-2 border-border py-2 text-sm font-semibold hover:border-success hover:text-success disabled:opacity-60"
        >
          👍 Ναι
        </button>
        <button
          type="button"
          onClick={() => send("thumbs_down")}
          disabled={status === "sending"}
          className="flex-1 rounded-full border-2 border-border py-2 text-sm font-semibold hover:border-danger hover:text-danger disabled:opacity-60"
        >
          👎 Όχι
        </button>
      </div>

      {!showCorrection ? (
        <button
          type="button"
          onClick={() => setShowCorrection(true)}
          className="text-xs text-muted hover:text-accent text-left font-medium"
        >
          Κάτι δεν είναι σωστό;
        </button>
      ) : (
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={() => send("closed")}
            disabled={status === "sending"}
            className="flex-1 rounded-full border-2 border-border py-1.5 text-xs font-semibold disabled:opacity-60"
          >
            Έκλεισε
          </button>
          <button
            type="button"
            onClick={() => send("wrong_info")}
            disabled={status === "sending"}
            className="flex-1 rounded-full border-2 border-border py-1.5 text-xs font-semibold disabled:opacity-60"
          >
            Λάθος στοιχεία
          </button>
        </div>
      )}

      {status === "error" && (
        <p className="text-xs text-danger">Κάτι πήγε στραβά, δοκίμασε ξανά.</p>
      )}
    </div>
  );
}
