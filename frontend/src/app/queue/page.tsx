"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getPatientQueue, ApiError } from "@/lib/api";
import type { QueueEntry } from "@/lib/types";
import {
  Users,
  Activity,
  Clock,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

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
    return iso;
  }
}

const STALE_THRESHOLD_MS = 2 * 60 * 60 * 1000; // 2 hours

function isStale(visitAt: string | null): boolean {
  if (!visitAt) return false;
  try {
    return Date.now() - new Date(visitAt).getTime() > STALE_THRESHOLD_MS;
  } catch {
    return false;
  }
}

export default function QueuePage() {
  const [entries, setEntries] = useState<QueueEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getPatientQueue();
      setEntries(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const noTriageCount = entries.filter((e) => e.latest_visit_id === null).length;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-navy">Patient Queue</h1>
          <p className="mt-1 text-navy/60">
            Today&apos;s patients with their latest triage status.
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

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {noTriageCount > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700 flex items-center gap-2">
          <AlertTriangle size={16} className="shrink-0" />
          {noTriageCount} patient{noTriageCount > 1 ? "s" : ""} today with no
          triage visit recorded.
        </div>
      )}

      {loading && entries.length === 0 ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
        </div>
      ) : entries.length === 0 ? (
        <div className="rounded-xl border border-navy/10 bg-white px-6 py-12 text-center">
          <Users size={32} className="mx-auto text-navy/20 mb-3" />
          <p className="text-navy/40 text-sm">
            No patients with visits today.
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
                  DOB
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">
                  ESI
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">
                  Final ESI
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Last Visit
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50">
                  Status
                </th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50" />
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => {
                const stale = isStale(e.latest_visit_at);
                return (
                  <tr
                    key={e.id}
                    className="border-b border-navy/5 last:border-0 hover:bg-navy/[0.02]"
                  >
                    <td className="px-5 py-3">
                      <Link
                        href={`/patients/${e.id}`}
                        className="font-medium text-navy hover:text-sky transition-colors"
                      >
                        {e.last_name}, {e.first_name}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-navy/60">{e.date_of_birth}</td>
                    <td className="px-5 py-3 text-center">
                      {e.latest_esi_level !== null ? (
                        <span
                          className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${esiColor(e.latest_esi_level)}`}
                        >
                          {e.latest_esi_level}
                        </span>
                      ) : (
                        <span className="text-xs text-navy/30">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-center">
                      {e.latest_final_esi !== null ? (
                        <span className="inline-block rounded-md border border-navy/20 bg-navy/5 px-2 py-0.5 text-xs font-medium text-navy">
                          {e.latest_final_esi}
                        </span>
                      ) : (
                        <span className="text-xs text-navy/30">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <span className="inline-flex items-center gap-1 text-xs text-navy/50">
                        <Clock size={12} />
                        {formatTime(e.latest_visit_at)}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {e.latest_disposition ? (
                        <span className="text-xs text-navy/60">
                          {e.latest_disposition}
                        </span>
                      ) : stale ? (
                        <span className="inline-flex items-center gap-1 text-xs text-amber-600">
                          <AlertTriangle size={12} />
                          May need re-triage
                        </span>
                      ) : e.latest_visit_id === null ? (
                        <span className="text-xs text-red-500">
                          No triage yet
                        </span>
                      ) : (
                        <span className="text-xs text-navy/30">Waiting</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Link
                        href={`/patients/${e.id}/triage`}
                        className="inline-flex items-center gap-1 rounded-lg border border-navy/15 px-3 py-1.5 text-xs text-navy transition-colors hover:bg-navy/5 cursor-pointer"
                      >
                        <Activity size={12} />
                        Triage
                      </Link>
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
