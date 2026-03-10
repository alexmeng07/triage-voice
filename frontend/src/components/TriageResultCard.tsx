import type { TriageVisitResponse } from "@/lib/types";
import Link from "next/link";
import { CheckCircle2, AlertTriangle, ShieldAlert } from "lucide-react";

interface Props {
  result: TriageVisitResponse;
  patientId: number;
  onNewVisit?: () => void;
}

function esiColor(level: number): string {
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

function esiLabel(level: number): string {
  switch (level) {
    case 1:
      return "Resuscitation";
    case 2:
      return "Emergent";
    case 3:
      return "Urgent";
    case 4:
      return "Less Urgent";
    case 5:
      return "Non-Urgent";
    default:
      return "Unknown";
  }
}

function HighAcuityAlert({ triage }: { triage: TriageVisitResponse["triage"] }) {
  const isEsi1 = triage.esi_level === 1;

  return (
    <div
      className={`rounded-xl border-2 px-5 py-4 space-y-3 ${
        isEsi1
          ? "border-red-400 bg-red-50"
          : "border-orange-400 bg-orange-50"
      }`}
    >
      <div className="flex items-start gap-3">
        <ShieldAlert
          size={24}
          className={`shrink-0 mt-0.5 ${isEsi1 ? "text-red-600" : "text-orange-600"}`}
        />
        <div>
          <p
            className={`font-semibold ${isEsi1 ? "text-red-800" : "text-orange-800"}`}
          >
            {isEsi1
              ? "Potential life-threatening emergency"
              : "High-risk situation identified"}
          </p>
          <p
            className={`text-sm mt-1 ${isEsi1 ? "text-red-700" : "text-orange-700"}`}
          >
            Follow your facility&apos;s emergency protocol immediately. Notify
            the RN/physician in charge.
          </p>
        </div>
      </div>

      {triage.red_flags.length > 0 && (
        <div className="flex flex-wrap gap-2 ml-9">
          {triage.red_flags.map((flag, i) => (
            <span
              key={i}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${
                isEsi1
                  ? "border-red-300 bg-red-100 text-red-800"
                  : "border-orange-300 bg-orange-100 text-orange-800"
              }`}
            >
              <AlertTriangle size={12} />
              {flag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function TriageResultCard({
  result,
  patientId,
  onNewVisit,
}: Props) {
  const { visit, triage } = result;
  const isHighAcuity = triage.esi_level <= 2;

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-sage-dark/40 bg-sage/20 px-5 py-4 flex items-center gap-3">
        <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
        <p className="text-sm font-medium text-navy">
          Triage visit recorded successfully (Visit #{visit.id})
        </p>
      </div>

      {isHighAcuity && <HighAcuityAlert triage={triage} />}

      <div className="rounded-xl border border-navy/10 bg-white p-6 space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h3 className="text-lg font-semibold text-navy">Triage Result</h3>
          <span
            className={`inline-block rounded-lg border px-3 py-1 text-sm font-semibold ${esiColor(triage.esi_level)}`}
          >
            ESI {triage.esi_level} — {esiLabel(triage.esi_level)}
          </span>
        </div>

        {!isHighAcuity && (
          <p className="text-sm text-navy/60 italic">
            Suggested priority for clinician review
          </p>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-xs font-medium text-navy/50 mb-1">Method</p>
            <p className="text-navy">{triage.method}</p>
          </div>
          {triage.confidence !== null && (
            <div>
              <p className="text-xs font-medium text-navy/50 mb-1">
                Confidence
              </p>
              <p className="text-navy">
                {(triage.confidence * 100).toFixed(0)}%
              </p>
            </div>
          )}
        </div>

        <div>
          <p className="text-xs font-medium text-navy/50 mb-1">Summary</p>
          <p className="text-sm text-navy/80">{triage.summary}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-navy/50 mb-1">
            Recommended Action
          </p>
          <p className="text-sm text-navy/80">{triage.recommended_action}</p>
        </div>

        {!isHighAcuity && triage.red_flags.length > 0 && (
          <div>
            <p className="text-xs font-medium text-navy/50 mb-1">Flags</p>
            <div className="flex flex-wrap gap-2">
              {triage.red_flags.map((flag, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700"
                >
                  <AlertTriangle size={12} />
                  {flag}
                </span>
              ))}
            </div>
          </div>
        )}

        {(visit.pain_score !== null || visit.onset || visit.symptom_location) && (
          <div className="border-t border-navy/10 pt-4">
            <p className="text-xs font-medium text-navy/50 mb-2">Structured Data</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
              {visit.pain_score !== null && (
                <div>
                  <p className="text-xs text-navy/40">Pain Score</p>
                  <p className="text-navy">{visit.pain_score}/10</p>
                </div>
              )}
              {visit.onset && (
                <div>
                  <p className="text-xs text-navy/40">Onset</p>
                  <p className="text-navy">{visit.onset}</p>
                </div>
              )}
              {visit.symptom_location && (
                <div>
                  <p className="text-xs text-navy/40">Location</p>
                  <p className="text-navy">{visit.symptom_location}</p>
                </div>
              )}
            </div>
          </div>
        )}

        <p className="text-xs text-navy/30 italic">{triage.disclaimer}</p>
      </div>

      <div className="flex gap-3">
        <Link
          href={`/patients/${patientId}`}
          className="inline-flex items-center gap-1.5 rounded-xl border border-navy/15 px-4 py-2 text-sm text-navy transition-colors hover:bg-navy/5 cursor-pointer"
        >
          Back to Patient
        </Link>
        {onNewVisit && (
          <button
            type="button"
            onClick={onNewVisit}
            className="rounded-xl bg-navy px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-navy-dark cursor-pointer"
          >
            New Triage Visit
          </button>
        )}
      </div>
    </div>
  );
}
