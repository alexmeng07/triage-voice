"use client";

import { useState } from "react";
import type { VisitResponse } from "@/lib/types";
import VisitDetailPanel from "./VisitDetailPanel";
import { Clock, ChevronDown, ChevronRight } from "lucide-react";

interface Props {
  visits: VisitResponse[];
  onVisitUpdated?: (updated: VisitResponse) => void;
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

function esiLabel(level: number | null): string {
  switch (level) {
    case 1:
      return "ESI 1 — Resuscitation";
    case 2:
      return "ESI 2 — Emergent";
    case 3:
      return "ESI 3 — Urgent";
    case 4:
      return "ESI 4 — Less Urgent";
    case 5:
      return "ESI 5 — Non-Urgent";
    default:
      return "Unrated";
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function VisitHistoryList({ visits, onVisitUpdated }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  if (visits.length === 0) {
    return (
      <div className="rounded-xl border border-navy/10 bg-white px-6 py-10 text-center">
        <p className="text-navy/40 text-sm">No visits recorded yet.</p>
      </div>
    );
  }

  function handleUpdated(updated: VisitResponse) {
    onVisitUpdated?.(updated);
  }

  return (
    <div className="space-y-3">
      {visits.map((v) => {
        const isExpanded = expandedId === v.id;
        return (
          <div key={v.id}>
            <button
              onClick={() => setExpandedId(isExpanded ? null : v.id)}
              className="w-full rounded-xl border border-navy/10 bg-white px-5 py-4 text-left transition-all hover:border-sky/40 cursor-pointer"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-2 flex-1 min-w-0">
                  {isExpanded ? (
                    <ChevronDown size={16} className="text-navy/30 shrink-0 mt-0.5" />
                  ) : (
                    <ChevronRight size={16} className="text-navy/30 shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${esiColor(v.esi_level)}`}
                      >
                        {esiLabel(v.esi_level)}
                      </span>
                      {v.final_esi_level !== null && (
                        <span className="inline-block rounded-md border border-navy/20 bg-navy/5 px-2 py-0.5 text-xs font-medium text-navy">
                          Final: ESI {v.final_esi_level}
                        </span>
                      )}
                      {v.triage_method && (
                        <span className="text-xs text-navy/40">
                          via {v.triage_method}
                        </span>
                      )}
                      {v.reviewed_by && (
                        <span className="text-xs text-emerald-600">
                          Reviewed
                        </span>
                      )}
                    </div>
                    {v.chief_complaint && (
                      <p className="mt-2 text-sm text-navy/70 line-clamp-2">
                        {v.chief_complaint}
                      </p>
                    )}
                    {v.triage_summary && (
                      <p className="mt-1 text-xs text-navy/50">
                        {v.triage_summary}
                      </p>
                    )}
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 text-xs text-navy/30 shrink-0">
                  <Clock size={12} />
                  {formatDate(v.created_at)}
                </span>
              </div>
            </button>

            {isExpanded && (
              <div className="mt-2 ml-4">
                <VisitDetailPanel visit={v} onUpdated={handleUpdated} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
