"use client";

import { useState } from "react";
import type { CreateVisitRequest } from "@/lib/types";
import { AlertTriangle } from "lucide-react";

interface Props {
  onSubmit: (data: CreateVisitRequest) => void;
  loading: boolean;
}

const ONSET_OPTIONS = [
  { value: "", label: "Select onset..." },
  { value: "< 1 hour", label: "Less than 1 hour ago" },
  { value: "1-6 hours", label: "1 to 6 hours ago" },
  { value: "6-24 hours", label: "6 to 24 hours ago" },
  { value: "1-3 days", label: "1 to 3 days ago" },
  { value: "> 3 days", label: "More than 3 days ago" },
  { value: "chronic", label: "Chronic / recurring" },
];

export default function TriageVisitForm({ onSubmit, loading }: Props) {
  const [transcript, setTranscript] = useState("");
  const [painScore, setPainScore] = useState<number | null>(null);
  const [onset, setOnset] = useState("");
  const [symptomLocation, setSymptomLocation] = useState("");
  const [showWarning, setShowWarning] = useState(false);

  function getMissingFields(): string[] {
    const missing: string[] = [];
    if (painScore === null) missing.push("Pain score");
    if (!onset) missing.push("Onset timeframe");
    return missing;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!transcript.trim()) return;

    const missingFields = getMissingFields();
    if (missingFields.length > 0 && !showWarning) {
      setShowWarning(true);
      return;
    }

    doSubmit();
  }

  function doSubmit() {
    setShowWarning(false);
    const data: CreateVisitRequest = {
      transcript_or_note: transcript.trim(),
    };
    if (painScore !== null) data.pain_score = painScore;
    if (onset) data.onset = onset;
    if (symptomLocation.trim()) data.symptom_location = symptomLocation.trim();
    onSubmit(data);
  }

  const fieldClass =
    "w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-xs font-medium text-navy/60 mb-1">
          Patient Transcript / Chief Complaint
        </label>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          rows={6}
          placeholder="Enter the patient's description of their symptoms, or paste a transcript..."
          className="w-full rounded-xl border border-navy/15 bg-white px-4 py-3 text-sm outline-none transition-colors focus:border-sky focus:ring-2 focus:ring-sky/20 placeholder:text-navy/30 resize-y"
        />
      </div>

      <div className="rounded-xl border border-navy/10 bg-white p-5 space-y-4">
        <p className="text-xs font-medium text-navy/50">
          Structured Fields (recommended)
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-navy/60 mb-1">
              Pain Score (0-10)
            </label>
            <select
              value={painScore === null ? "" : String(painScore)}
              onChange={(e) =>
                setPainScore(e.target.value === "" ? null : Number(e.target.value))
              }
              className={fieldClass}
            >
              <option value="">Not assessed</option>
              {Array.from({ length: 11 }, (_, i) => (
                <option key={i} value={String(i)}>
                  {i} {i === 0 ? "— No pain" : i <= 3 ? "— Mild" : i <= 6 ? "— Moderate" : "— Severe"}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-navy/60 mb-1">
              Onset
            </label>
            <select
              value={onset}
              onChange={(e) => setOnset(e.target.value)}
              className={fieldClass}
            >
              {ONSET_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-navy/60 mb-1">
              Symptom Location
            </label>
            <input
              type="text"
              value={symptomLocation}
              onChange={(e) => setSymptomLocation(e.target.value)}
              placeholder="e.g. chest, abdomen, head"
              className={`${fieldClass} placeholder:text-navy/30`}
            />
          </div>
        </div>
      </div>

      {showWarning && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 space-y-3">
          <div className="flex items-start gap-2">
            <AlertTriangle size={18} className="text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Some recommended fields are empty
              </p>
              <ul className="mt-1 text-sm text-amber-700 list-disc list-inside">
                {getMissingFields().map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="flex gap-3 ml-6">
            <button
              type="button"
              onClick={() => setShowWarning(false)}
              className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-800 transition-colors hover:bg-amber-50 cursor-pointer"
            >
              Fill in details
            </button>
            <button
              type="button"
              onClick={doSubmit}
              className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-700 cursor-pointer"
            >
              Proceed anyway
            </button>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !transcript.trim()}
        className="rounded-xl bg-navy px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-dark disabled:opacity-40 cursor-pointer"
      >
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Running triage...
          </span>
        ) : (
          "Submit for Triage"
        )}
      </button>
    </form>
  );
}
