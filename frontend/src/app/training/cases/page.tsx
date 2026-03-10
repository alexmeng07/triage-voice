"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTrainingCases, attemptTrainingCase, ApiError } from "@/lib/api";
import type { TrainingCase, TrainingAttemptResult } from "@/lib/types";
import {
  BookOpen,
  Play,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  BarChart3,
  AlertTriangle,
  ShieldAlert,
} from "lucide-react";

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

export default function TrainingCasesPage() {
  const [cases, setCases] = useState<TrainingCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<TrainingCase | null>(null);
  const [attemptResult, setAttemptResult] = useState<TrainingAttemptResult | null>(null);
  const [attempting, setAttempting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getTrainingCases();
        setCases(data);
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load training cases");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleAttempt(c: TrainingCase) {
    setAttempting(true);
    setAttemptResult(null);
    setError(null);
    try {
      const result = await attemptTrainingCase(c.id);
      setAttemptResult(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Attempt failed");
    } finally {
      setAttempting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
      </div>
    );
  }

  if (selectedCase) {
    return (
      <div className="space-y-6 max-w-3xl">
        <button
          onClick={() => {
            setSelectedCase(null);
            setAttemptResult(null);
          }}
          className="inline-flex items-center gap-1.5 text-sm text-navy/60 hover:text-navy transition-colors cursor-pointer"
        >
          <ArrowLeft size={16} />
          Back to cases
        </button>

        <div className="rounded-xl border border-navy/10 bg-white p-6 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-navy">{selectedCase.title}</h2>
              <p className="text-sm text-navy/60 mt-1">{selectedCase.description}</p>
            </div>
            {selectedCase.category && (
              <span className="text-xs bg-navy/5 text-navy/60 px-2 py-1 rounded-md shrink-0">
                {selectedCase.category}
              </span>
            )}
          </div>

          <div>
            <p className="text-xs font-medium text-navy/50 mb-1">Transcript</p>
            <div className="rounded-lg bg-cream border border-navy/10 px-4 py-3 text-sm text-navy/80">
              {selectedCase.transcript}
            </div>
          </div>

          {!attemptResult && (
            <button
              onClick={() => handleAttempt(selectedCase)}
              disabled={attempting}
              className="inline-flex items-center gap-2 rounded-xl bg-navy px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-dark disabled:opacity-40 cursor-pointer"
            >
              {attempting ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Running triage...
                </>
              ) : (
                <>
                  <Play size={16} />
                  Practice Triage
                </>
              )}
            </button>
          )}

          {attemptResult && (
            <div className="space-y-4 border-t border-navy/10 pt-4">
              <div className="flex items-center gap-3">
                {attemptResult.matched ? (
                  <CheckCircle2 size={20} className="text-emerald-600" />
                ) : (
                  <XCircle size={20} className="text-red-500" />
                )}
                <p className="text-sm font-medium text-navy">
                  {attemptResult.matched
                    ? "Engine matched the expected triage level"
                    : "Engine did not match the expected level"}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg border border-navy/10 p-4 text-center">
                  <p className="text-xs text-navy/50 mb-1">Engine Result</p>
                  <span
                    className={`inline-block rounded-md border px-3 py-1 text-sm font-semibold ${esiColor(attemptResult.triage.esi_level)}`}
                  >
                    ESI {attemptResult.triage.esi_level}
                  </span>
                  <p className="text-xs text-navy/40 mt-2">via {attemptResult.triage.method}</p>
                </div>
                <div className="rounded-lg border border-navy/10 p-4 text-center">
                  <p className="text-xs text-navy/50 mb-1">Expected (Training)</p>
                  <span
                    className={`inline-block rounded-md border px-3 py-1 text-sm font-semibold ${esiColor(attemptResult.expected_esi)}`}
                  >
                    ESI {attemptResult.expected_esi}
                  </span>
                </div>
              </div>

              {attemptResult.triage.red_flags.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-navy/50 mb-1">Flags Detected</p>
                  <div className="flex flex-wrap gap-2">
                    {attemptResult.triage.red_flags.map((flag, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700"
                      >
                        {attemptResult.triage.esi_level <= 2 ? (
                          <ShieldAlert size={12} />
                        ) : (
                          <AlertTriangle size={12} />
                        )}
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <p className="text-xs font-medium text-navy/50 mb-1">Engine Summary</p>
                <p className="text-sm text-navy/70">{attemptResult.triage.summary}</p>
              </div>

              {selectedCase.rationale && (
                <div className="rounded-lg border border-sky/30 bg-sky/10 px-4 py-3">
                  <p className="text-xs font-medium text-navy/50 mb-1">
                    Educational Rationale
                  </p>
                  <p className="text-sm text-navy/70">{selectedCase.rationale}</p>
                </div>
              )}

              <button
                onClick={() => setAttemptResult(null)}
                className="rounded-xl border border-navy/15 px-4 py-2 text-sm text-navy transition-colors hover:bg-navy/5 cursor-pointer"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-navy">Training Cases</h1>
          <p className="mt-1 text-navy/60">
            Practice triage on curated clinical scenarios. Select a case to view
            the transcript, run the triage engine, and compare against the
            expected ESI level.
          </p>
        </div>
        <Link
          href="/training/stats"
          className="inline-flex items-center gap-2 rounded-xl border border-navy/15 px-4 py-2 text-sm text-navy transition-colors hover:bg-navy/5 shrink-0 cursor-pointer"
        >
          <BarChart3 size={16} />
          View Stats
        </Link>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {cases.length === 0 ? (
        <div className="rounded-xl border border-navy/10 bg-white px-6 py-12 text-center">
          <BookOpen size={32} className="mx-auto text-navy/20 mb-3" />
          <p className="text-navy/40 text-sm">No training cases available.</p>
          <p className="text-navy/30 text-xs mt-1">
            Run the seed script to populate training cases.
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {cases.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCase(c)}
              className="w-full flex items-center gap-4 rounded-xl border border-navy/10 bg-white px-5 py-4 text-left transition-all hover:border-sky hover:shadow-sm cursor-pointer"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sky/15 text-navy">
                <BookOpen size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-navy truncate">{c.title}</p>
                <p className="text-xs text-navy/50 mt-0.5 line-clamp-1">
                  {c.description}
                </p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {c.category && (
                  <span className="text-xs bg-navy/5 text-navy/50 px-2 py-0.5 rounded-md">
                    {c.category}
                  </span>
                )}
                <span
                  className={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${esiColor(c.target_esi)}`}
                >
                  Target ESI {c.target_esi}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
