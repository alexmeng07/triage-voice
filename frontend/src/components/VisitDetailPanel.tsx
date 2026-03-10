"use client";

import type { VisitResponse } from "@/lib/types";
import VisitReviewForm from "./VisitReviewForm";
import { AlertTriangle, ShieldAlert, Printer } from "lucide-react";

interface Props {
  visit: VisitResponse;
  onUpdated: (updated: VisitResponse) => void;
}

function esiColor(level: number | null): string {
  switch (level) {
    case 1:
      return "bg-red-100 text-red-700 border-red-200";
    case 2:
      return "bg-orange-100 text-orange-700 border-orange-200";
    case 3:
      return "bg-amber-100 text-amber-700 border-amber-200";
    case 4:
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case 5:
      return "bg-sky/20 text-navy border-sky/30";
    default:
      return "bg-gray-100 text-gray-600 border-gray-200";
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function VisitDetailPanel({ visit, onUpdated }: Props) {
  const isHighAcuity = visit.esi_level !== null && visit.esi_level <= 2;

  function handlePrint() {
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`
      <html><head><title>Visit #${visit.id} Summary</title>
      <style>body{font-family:Georgia,serif;max-width:700px;margin:2em auto;color:#1a1a2e}
      h1{font-size:1.3em}h2{font-size:1em;margin-top:1.5em;border-bottom:1px solid #ddd;padding-bottom:4px}
      .label{font-size:0.8em;color:#666;margin-bottom:2px}.value{margin-bottom:12px}
      .disclaimer{font-size:0.75em;color:#999;margin-top:2em;font-style:italic;border-top:1px solid #eee;padding-top:8px}</style>
      </head><body>
      <h1>Visit Summary #${visit.id}</h1>
      <div class="label">Date</div><div class="value">${formatDate(visit.created_at)}</div>
      ${visit.esi_level !== null ? `<div class="label">Suggested ESI Level</div><div class="value">ESI ${visit.esi_level}${visit.triage_method ? ` (${visit.triage_method})` : ""}</div>` : ""}
      ${visit.final_esi_level !== null ? `<div class="label">Clinician ESI Level</div><div class="value">ESI ${visit.final_esi_level}</div>` : ""}
      <h2>Chief Complaint</h2>
      <div class="value">${visit.chief_complaint || "N/A"}</div>
      ${visit.triage_summary ? `<h2>Triage Summary</h2><div class="value">${visit.triage_summary}</div>` : ""}
      ${visit.recommended_action ? `<h2>Recommended Action</h2><div class="value">${visit.recommended_action}</div>` : ""}
      ${visit.pain_score !== null ? `<div class="label">Pain Score</div><div class="value">${visit.pain_score}/10</div>` : ""}
      ${visit.onset ? `<div class="label">Onset</div><div class="value">${visit.onset}</div>` : ""}
      ${visit.symptom_location ? `<div class="label">Symptom Location</div><div class="value">${visit.symptom_location}</div>` : ""}
      ${visit.reviewed_by ? `<h2>Clinician Review</h2><div class="label">Reviewed By</div><div class="value">${visit.reviewed_by}${visit.reviewed_role ? ` (${visit.reviewed_role})` : ""}</div>` : ""}
      ${visit.disposition ? `<div class="label">Disposition</div><div class="value">${visit.disposition}</div>` : ""}
      <div class="disclaimer">This is a training and documentation aid, not medical advice or a clinical decision support tool.</div>
      </body></html>
    `);
    win.document.close();
    win.print();
  }

  return (
    <div className="rounded-xl border border-navy/10 bg-white p-5 space-y-5">
      {isHighAcuity && (
        <div
          className={`rounded-lg border px-4 py-3 flex items-start gap-2 ${
            visit.esi_level === 1
              ? "border-red-300 bg-red-50"
              : "border-orange-300 bg-orange-50"
          }`}
        >
          <ShieldAlert
            size={16}
            className={`shrink-0 mt-0.5 ${visit.esi_level === 1 ? "text-red-600" : "text-orange-600"}`}
          />
          <p
            className={`text-sm ${visit.esi_level === 1 ? "text-red-700" : "text-orange-700"}`}
          >
            {visit.esi_level === 1
              ? "ESI 1 — life-threatening presentation identified"
              : "ESI 2 — high-risk situation identified"}
          </p>
        </div>
      )}

      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-navy/40">Visit #{visit.id}</p>
          <p className="text-xs text-navy/40">{formatDate(visit.created_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          {visit.esi_level !== null && (
            <span
              className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${esiColor(visit.esi_level)}`}
            >
              ESI {visit.esi_level}
            </span>
          )}
          {visit.final_esi_level !== null && (
            <span className="inline-block rounded-md border border-navy/20 bg-navy/5 px-2 py-0.5 text-xs font-medium text-navy">
              Final: ESI {visit.final_esi_level}
            </span>
          )}
          <button
            onClick={handlePrint}
            className="p-1.5 rounded-md text-navy/40 hover:text-navy hover:bg-navy/5 transition-colors cursor-pointer"
            title="Print visit summary"
          >
            <Printer size={14} />
          </button>
        </div>
      </div>

      {visit.chief_complaint && (
        <div>
          <p className="text-xs font-medium text-navy/50 mb-1">
            Chief Complaint / Transcript
          </p>
          <p className="text-sm text-navy/70">{visit.chief_complaint}</p>
        </div>
      )}

      {visit.triage_summary && (
        <div>
          <p className="text-xs font-medium text-navy/50 mb-1">Summary</p>
          <p className="text-sm text-navy/70">{visit.triage_summary}</p>
        </div>
      )}

      {visit.recommended_action && (
        <div>
          <p className="text-xs font-medium text-navy/50 mb-1">
            Recommended Action
          </p>
          <p className="text-sm text-navy/70">{visit.recommended_action}</p>
        </div>
      )}

      {(visit.pain_score !== null || visit.onset || visit.symptom_location) && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {visit.pain_score !== null && (
            <div>
              <p className="text-xs text-navy/40">Pain Score</p>
              <p className="text-sm text-navy">{visit.pain_score}/10</p>
            </div>
          )}
          {visit.onset && (
            <div>
              <p className="text-xs text-navy/40">Onset</p>
              <p className="text-sm text-navy">{visit.onset}</p>
            </div>
          )}
          {visit.symptom_location && (
            <div>
              <p className="text-xs text-navy/40">Location</p>
              <p className="text-sm text-navy">{visit.symptom_location}</p>
            </div>
          )}
        </div>
      )}

      {visit.triage_method && (
        <div className="flex gap-4 text-xs text-navy/40">
          <span>Method: {visit.triage_method}</span>
        </div>
      )}

      {visit.disposition && (
        <div className="flex items-center gap-1 text-xs text-navy/50">
          <AlertTriangle size={12} />
          Disposition: {visit.disposition}
        </div>
      )}

      <div className="border-t border-navy/10 pt-4">
        <VisitReviewForm visit={visit} onUpdated={onUpdated} />
      </div>
    </div>
  );
}
