"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTrainingStats, ApiError } from "@/lib/api";
import type { TrainingStats } from "@/lib/types";
import { ArrowLeft, BarChart3 } from "lucide-react";

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

export default function TrainingStatsPage() {
  const [stats, setStats] = useState<TrainingStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getTrainingStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load stats");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const totalAttempts = stats.reduce((s, r) => s + (r.attempts || 0), 0);
  const totalMatches = stats.reduce((s, r) => s + (r.matches || 0), 0);
  const overallRate = totalAttempts > 0 ? ((totalMatches / totalAttempts) * 100).toFixed(0) : "—";

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
        href="/training/cases"
        className="inline-flex items-center gap-1.5 text-sm text-navy/60 hover:text-navy transition-colors"
      >
        <ArrowLeft size={16} />
        Back to cases
      </Link>

      <div>
        <h1 className="text-2xl font-semibold text-navy">Training Statistics</h1>
        <p className="mt-1 text-navy/60">
          Aggregate performance of the triage engine against training case
          expectations.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-navy/10 bg-white p-5 text-center">
          <p className="text-xs text-navy/50 mb-1">Total Attempts</p>
          <p className="text-2xl font-semibold text-navy">{totalAttempts}</p>
        </div>
        <div className="rounded-xl border border-navy/10 bg-white p-5 text-center">
          <p className="text-xs text-navy/50 mb-1">Matches</p>
          <p className="text-2xl font-semibold text-emerald-600">{totalMatches}</p>
        </div>
        <div className="rounded-xl border border-navy/10 bg-white p-5 text-center">
          <p className="text-xs text-navy/50 mb-1">Agreement Rate</p>
          <p className="text-2xl font-semibold text-navy">{overallRate}%</p>
        </div>
      </div>

      {stats.length === 0 ? (
        <div className="rounded-xl border border-navy/10 bg-white px-6 py-12 text-center">
          <BarChart3 size={32} className="mx-auto text-navy/20 mb-3" />
          <p className="text-navy/40 text-sm">No training data yet.</p>
          <p className="text-navy/30 text-xs mt-1">
            Practice some training cases to see statistics here.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-navy/10 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy/10 text-left">
                <th className="px-5 py-3 text-xs font-medium text-navy/50">Case</th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">Target ESI</th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">Attempts</th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">Matches</th>
                <th className="px-5 py-3 text-xs font-medium text-navy/50 text-center">Rate</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((s) => {
                const rate =
                  s.attempts > 0
                    ? ((s.matches / s.attempts) * 100).toFixed(0)
                    : "—";
                return (
                  <tr key={s.case_id} className="border-b border-navy/5 last:border-0">
                    <td className="px-5 py-3 text-navy">{s.title}</td>
                    <td className="px-5 py-3 text-center">
                      <span
                        className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${esiColor(s.target_esi)}`}
                      >
                        ESI {s.target_esi}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-center text-navy/70">{s.attempts || 0}</td>
                    <td className="px-5 py-3 text-center text-emerald-600">{s.matches || 0}</td>
                    <td className="px-5 py-3 text-center text-navy/70">{rate}%</td>
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
