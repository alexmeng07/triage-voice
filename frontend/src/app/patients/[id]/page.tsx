"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { getPatient, getPatientVisits, ApiError } from "@/lib/api";
import type { PatientResponse, VisitResponse } from "@/lib/types";
import PatientHeaderCard from "@/components/PatientHeaderCard";
import VisitHistoryList from "@/components/VisitHistoryList";
import { Activity, ArrowLeft } from "lucide-react";

export default function PatientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const patientId = Number(id);

  const [patient, setPatient] = useState<PatientResponse | null>(null);
  const [visits, setVisits] = useState<VisitResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [p, v] = await Promise.all([
          getPatient(patientId),
          getPatientVisits(patientId),
        ]);
        setPatient(p);
        setVisits(v);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.detail : "Failed to load patient",
        );
      } finally {
        setLoading(false);
      }
    }
    if (patientId) load();
  }, [patientId]);

  function handleVisitUpdated(updated: VisitResponse) {
    setVisits((prev) =>
      prev.map((v) => (v.id === updated.id ? updated : v)),
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="space-y-4">
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || "Patient not found"}
        </div>
        <Link
          href="/patients"
          className="text-sm text-navy/60 hover:text-navy transition-colors"
        >
          &larr; Back to search
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <Link
        href="/patients"
        className="inline-flex items-center gap-1.5 text-sm text-navy/60 hover:text-navy transition-colors"
      >
        <ArrowLeft size={16} />
        Back to search
      </Link>

      <PatientHeaderCard patient={patient} />

      <div className="flex gap-3">
        <Link
          href={`/patients/${patient.id}/triage`}
          className="inline-flex items-center gap-2 rounded-xl bg-navy px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-dark cursor-pointer"
        >
          <Activity size={16} />
          Start Triage Visit
        </Link>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-navy mb-4">Visit History</h2>
        <VisitHistoryList
          visits={visits}
          onVisitUpdated={handleVisitUpdated}
        />
      </section>
    </div>
  );
}
