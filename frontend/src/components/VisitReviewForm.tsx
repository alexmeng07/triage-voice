"use client";

import { useState } from "react";
import type { VisitResponse, VisitReviewRequest } from "@/lib/types";
import { reviewVisit, ApiError } from "@/lib/api";
import { ClipboardCheck } from "lucide-react";

interface Props {
  visit: VisitResponse;
  onUpdated: (updated: VisitResponse) => void;
}

const DISPOSITION_OPTIONS = [
  "",
  "Sent to ED bed",
  "Sent to waiting room",
  "Sent to fast track",
  "Referred to specialist",
  "Discharged with instructions",
  "Left without being seen",
  "Other",
];

export default function VisitReviewForm({ visit, onUpdated }: Props) {
  const [reviewedBy, setReviewedBy] = useState(visit.reviewed_by || "");
  const [reviewedRole, setReviewedRole] = useState(visit.reviewed_role || "");
  const [finalEsi, setFinalEsi] = useState<number | null>(visit.final_esi_level);
  const [disposition, setDisposition] = useState(visit.disposition || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    const payload: VisitReviewRequest = {
      reviewed_by: reviewedBy.trim() || null,
      reviewed_role: reviewedRole.trim() || null,
      final_esi_level: finalEsi,
      disposition: disposition.trim() || null,
    };

    try {
      const updated = await reviewVisit(visit.id, payload);
      onUpdated(updated);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  const fieldClass =
    "w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20";

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <div className="flex items-center gap-2">
        <ClipboardCheck size={16} className="text-navy/50" />
        <p className="text-xs font-medium text-navy/50">
          Clinician Review
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Reviewed By
          </label>
          <input
            type="text"
            value={reviewedBy}
            onChange={(e) => setReviewedBy(e.target.value)}
            placeholder="Clinician name"
            className={`${fieldClass} placeholder:text-navy/30`}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Role
          </label>
          <input
            type="text"
            value={reviewedRole}
            onChange={(e) => setReviewedRole(e.target.value)}
            placeholder="e.g. RN, MD, PA"
            className={`${fieldClass} placeholder:text-navy/30`}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Final ESI Level
          </label>
          <select
            value={finalEsi === null ? "" : String(finalEsi)}
            onChange={(e) =>
              setFinalEsi(e.target.value === "" ? null : Number(e.target.value))
            }
            className={fieldClass}
          >
            <option value="">Not assigned</option>
            <option value="1">ESI 1 — Resuscitation</option>
            <option value="2">ESI 2 — Emergent</option>
            <option value="3">ESI 3 — Urgent</option>
            <option value="4">ESI 4 — Less Urgent</option>
            <option value="5">ESI 5 — Non-Urgent</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Disposition
          </label>
          <select
            value={disposition}
            onChange={(e) => setDisposition(e.target.value)}
            className={fieldClass}
          >
            {DISPOSITION_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt || "Select disposition..."}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-navy px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-navy-dark disabled:opacity-40 cursor-pointer"
        >
          {saving ? "Saving..." : "Save Review"}
        </button>
        {success && (
          <span className="text-xs text-emerald-600">Saved successfully</span>
        )}
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    </form>
  );
}
