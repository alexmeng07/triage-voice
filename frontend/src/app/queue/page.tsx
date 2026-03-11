"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getQueue,
  getQueueSummary,
  updateVisitStatus,
  ApiError,
} from "@/lib/api";
import type { QueueVisitEntry, QueueSummary } from "@/lib/types";
import { RefreshCw, Users } from "lucide-react";

const STATUS_LABELS: Record<string, string> = {
  waiting: "Waiting",
  in_triage: "In Triage",
  triaged: "Triaged",
  with_doctor: "With Doctor",
  complete: "Complete",
};

const STATUS_FLOW: Record<string, string | null> = {
  waiting: "in_triage",
  in_triage: "triaged",
  triaged: "with_doctor",
  with_doctor: "complete",
  complete: null,
};

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

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(iso).slice(0, 5);
  }
}

function formatWait(min: number | null): string {
  if (min === null || min === undefined) return "—";
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export default function QueuePage() {
  const [entries, setEntries] = useState<QueueVisitEntry[]>([]);
  const [summary, setSummary] = useState<QueueSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [queueData, summaryData] = await Promise.all([
        getQueue(),
        getQueueSummary(),
      ]);
      setEntries(queueData);
      setSummary(summaryData);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAdvance(e: QueueVisitEntry) {
    const next = STATUS_FLOW[e.status];
    if (!next) return;
    setUpdatingId(e.visit_id);
    try {
      await updateVisitStatus(e.visit_id, next);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to update status");
    } finally {
      setUpdatingId(null);
    }
  }

  const totalActive =
    summary &&
    summary.waiting +
      summary.in_triage +
      summary.triaged +
      summary.with_doctor;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-navy">Visit Queue</h1>
          <p className="mt-1 text-navy/60">
            Active visits by acuity. Update status as patients move through triage.
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-navy/15 px-4 py-2 text-sm text-navy transition-colors hover:bg-navy/5 cursor-pointer disabled:opacity-40"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {summary && totalActive !== undefined && totalActive > 0 && (
        <div className="flex flex-wrap gap-4 text-sm">
          <span className="text-navy/60">
            Waiting: <strong className="text-navy">{summary.waiting}</strong>
          </span>
          <span className="text-navy/60">
            In triage: <strong className="text-navy">{summary.in_triage}</strong>
          </span>
          <span className="text-navy/60">
            Triaged: <strong className="text-navy">{summary.triaged}</strong>
          </span>
          <span className="text-navy/60">
            With doctor: <strong className="text-navy">{summary.with_doctor}</strong>
          </span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && entries.length === 0 ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
        </div>
      ) : entries.length === 0 ? (
        <div className="rounded-xl border border-navy/10 bg-white px-6 py-12 text-center">
          <Users size={32} className="mx-auto text-navy/20 mb-3" />
          <p className="text-navy/40 text-sm">No active visits in queue.</p>
          <p className="mt-1 text-navy/30 text-xs">
            Create a triage visit from a patient record to add visits here.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-navy/10 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy/10 text-left">
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Patient
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Complaint
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">
                  ESI
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Status
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Arrival
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Wait
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 w-32">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => {
                const nextStatus = STATUS_FLOW[e.status];
                const isUpdating = updatingId === e.visit_id;
                return (
                  <tr
                    key={e.visit_id}
                    className="border-b border-navy/5 last:border-0 hover:bg-navy/[0.02]"
                  >
                    <td className="px-5 py-3">
                      <Link
                        href={`/patients/${e.patient_id}`}
                        className="font-medium text-navy hover:text-sky transition-colors"
                      >
                        {e.patient_name}
                      </Link>
                      <span className="ml-1.5 text-xs text-navy/40">
                        {e.date_of_birth}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-navy/70 max-w-[200px] truncate">
                      {e.chief_complaint || "—"}
                    </td>
                    <td className="px-5 py-3 text-center">
                      {e.esi_level !== null ? (
                        <span
                          className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${esiColor(e.esi_level)}`}
                        >
                          {e.esi_level}
                        </span>
                      ) : (
                        <span className="text-xs text-navy/30">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-xs text-navy/70">
                        {STATUS_LABELS[e.status] ?? e.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs text-navy/50">
                      {formatTime(e.arrival_time)}
                    </td>
                    <td className="px-5 py-3 text-xs text-navy/60">
                      {formatWait(e.wait_minutes)}
                    </td>
                    <td className="px-5 py-3">
                      {nextStatus && (
                        <button
                          onClick={() => handleAdvance(e)}
                          disabled={isUpdating}
                          className="inline-flex items-center gap-1 rounded-lg border border-navy/15 px-3 py-1.5 text-xs text-navy transition-colors hover:bg-navy/5 cursor-pointer disabled:opacity-50"
                        >
                          {isUpdating ? (
                            <span className="animate-pulse">Updating…</span>
                          ) : (
                            <>→ {STATUS_LABELS[nextStatus]}</>
                          )}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
