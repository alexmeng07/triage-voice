"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getEsiDistribution, getCommonComplaints, ApiError } from "@/lib/api";
import type { EsiDistribution, ComplaintCount } from "@/lib/types";
import { ArrowLeft, BarChart3 } from "lucide-react";

function esiColor(level: number | null): string {
  switch (level) {
    case 1:
      return "bg-red-100 text-red-700";
    case 2:
      return "bg-orange-100 text-orange-700";
    case 3:
      return "bg-amber-100 text-amber-700";
    case 4:
      return "bg-emerald-100 text-emerald-700";
    case 5:
      return "bg-sky/20 text-navy";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

function esiBarColor(level: number | null): string {
  switch (level) {
    case 1:
      return "bg-red-400";
    case 2:
      return "bg-orange-400";
    case 3:
      return "bg-amber-400";
    case 4:
      return "bg-emerald-400";
    case 5:
      return "bg-sky";
    default:
      return "bg-gray-300";
  }
}

export default function AdminStatsPage() {
  const [esiDist, setEsiDist] = useState<EsiDistribution[]>([]);
  const [complaints, setComplaints] = useState<ComplaintCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [esi, cc] = await Promise.all([
          getEsiDistribution(),
          getCommonComplaints(10),
        ]);
        setEsiDist(esi);
        setComplaints(cc);
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const totalVisits = esiDist.reduce((s, e) => s + e.count, 0);
  const highAcuityCount = esiDist
    .filter((e) => e.esi_level !== null && e.esi_level <= 2)
    .reduce((s, e) => s + e.count, 0);
  const highAcuityRate =
    totalVisits > 0 ? ((highAcuityCount / totalVisits) * 100).toFixed(1) : "0";
  const maxEsiCount = Math.max(...esiDist.map((e) => e.count), 1);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-navy/60 hover:text-navy transition-colors"
      >
        <ArrowLeft size={16} />
        Back to home
      </Link>

      <div>
        <h1 className="text-2xl font-semibold text-navy">Analytics</h1>
        <p className="mt-1 text-navy/60">
          Internal aggregate statistics for quality monitoring and system
          calibration. Not for individual staff performance tracking.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-navy/10 bg-white p-5 text-center">
          <p className="text-xs text-navy/50 mb-1">Total Visits</p>
          <p className="text-2xl font-semibold text-navy">{totalVisits}</p>
        </div>
        <div className="rounded-xl border border-navy/10 bg-white p-5 text-center">
          <p className="text-xs text-navy/50 mb-1">ESI 1-2 (High Acuity)</p>
          <p className="text-2xl font-semibold text-red-600">{highAcuityCount}</p>
        </div>
        <div className="rounded-xl border border-navy/10 bg-white p-5 text-center">
          <p className="text-xs text-navy/50 mb-1">High Acuity Rate</p>
          <p className="text-2xl font-semibold text-navy">{highAcuityRate}%</p>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-navy mb-4">ESI Distribution</h2>
        {esiDist.length === 0 ? (
          <div className="rounded-xl border border-navy/10 bg-white px-6 py-10 text-center">
            <BarChart3 size={32} className="mx-auto text-navy/20 mb-3" />
            <p className="text-sm text-navy/40">No visit data yet.</p>
          </div>
        ) : (
          <div className="rounded-xl border border-navy/10 bg-white p-5 space-y-3">
            {[1, 2, 3, 4, 5].map((level) => {
              const entry = esiDist.find((e) => e.esi_level === level);
              const count = entry?.count || 0;
              const pct = totalVisits > 0 ? ((count / totalVisits) * 100).toFixed(1) : "0";
              const barWidth = (count / maxEsiCount) * 100;
              return (
                <div key={level} className="flex items-center gap-3">
                  <span
                    className={`shrink-0 w-16 text-center rounded-md px-2 py-0.5 text-xs font-medium ${esiColor(level)}`}
                  >
                    ESI {level}
                  </span>
                  <div className="flex-1 h-6 bg-gray-100 rounded-md overflow-hidden">
                    <div
                      className={`h-full rounded-md transition-all ${esiBarColor(level)}`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <span className="text-sm text-navy/60 w-16 text-right shrink-0">
                    {count} ({pct}%)
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-navy mb-4">
          Most Common Complaints
        </h2>
        {complaints.length === 0 ? (
          <div className="rounded-xl border border-navy/10 bg-white px-6 py-10 text-center">
            <p className="text-sm text-navy/40">No complaint data yet.</p>
          </div>
        ) : (
          <div className="rounded-xl border border-navy/10 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-navy/10 text-left">
                  <th className="px-5 py-3 text-xs font-medium text-navy/50">#</th>
                  <th className="px-5 py-3 text-xs font-medium text-navy/50">
                    Complaint
                  </th>
                  <th className="px-5 py-3 text-xs font-medium text-navy/50 text-right">
                    Count
                  </th>
                </tr>
              </thead>
              <tbody>
                {complaints.map((c, i) => (
                  <tr
                    key={i}
                    className="border-b border-navy/5 last:border-0"
                  >
                    <td className="px-5 py-3 text-navy/40">{i + 1}</td>
                    <td className="px-5 py-3 text-navy line-clamp-1">
                      {c.chief_complaint}
                    </td>
                    <td className="px-5 py-3 text-right text-navy/70">
                      {c.count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
