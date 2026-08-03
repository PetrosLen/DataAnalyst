"use client";

import { useState } from "react";
import { submitFeedback, type FeedbackType } from "@/lib/api";
import { getSessionId } from "@/lib/session";

export default function FeedbackWidget({ venueSlug }: { venueSlug: string }) {
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [showCorrection, setShowCorrection] = useState(false);

  async function send(feedbackType: FeedbackType) {
    setStatus("sending");
    try {
      await submitFeedback({ sessionId: getSessionId(), venueSlug, feedbackType });
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") {
    return (
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3 text-sm text-neutral-300">
        Ευχαριστούμε για το feedback! 🙌
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3 flex flex-col gap-2">
      <p className="text-sm text-neutral-300">Ήταν καλή πρόταση;</p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => send("thumbs_up")}
          disabled={status === "sending"}
          className="flex-1 rounded-lg border border-neutral-700 py-2 text-sm hover:border-emerald-400 hover:text-emerald-400 disabled:opacity-60"
        >
          👍 Ναι
        </button>
        <button
          type="button"
          onClick={() => send("thumbs_down")}
          disabled={status === "sending"}
          className="flex-1 rounded-lg border border-neutral-700 py-2 text-sm hover:border-red-400 hover:text-red-400 disabled:opacity-60"
        >
          👎 Όχι
        </button>
      </div>

      {!showCorrection ? (
        <button
          type="button"
          onClick={() => setShowCorrection(true)}
          className="text-xs text-neutral-500 hover:text-neutral-300 text-left"
        >
          Κάτι δεν είναι σωστό;
        </button>
      ) : (
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={() => send("closed")}
            disabled={status === "sending"}
            className="flex-1 rounded-lg border border-neutral-700 py-1.5 text-xs disabled:opacity-60"
          >
            Έκλεισε
          </button>
          <button
            type="button"
            onClick={() => send("wrong_info")}
            disabled={status === "sending"}
            className="flex-1 rounded-lg border border-neutral-700 py-1.5 text-xs disabled:opacity-60"
          >
            Λάθος στοιχεία
          </button>
        </div>
      )}

      {status === "error" && (
        <p className="text-xs text-red-400">Κάτι πήγε στραβά, δοκίμασε ξανά.</p>
      )}
    </div>
  );
}
