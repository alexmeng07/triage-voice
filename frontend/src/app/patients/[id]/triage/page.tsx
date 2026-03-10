"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { getPatient, createTriageVisit, ApiError } from "@/lib/api";
import type { PatientResponse, TriageVisitResponse, CreateVisitRequest } from "@/lib/types";
import PatientHeaderCard from "@/components/PatientHeaderCard";
import TriageVisitForm from "@/components/TriageVisitForm";
import TriageResultCard from "@/components/TriageResultCard";
import { ArrowLeft } from "lucide-react";

export default function TriagePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const patientId = Number(id);

  const [patient, setPatient] = useState<PatientResponse | null>(null);
  const [result, setResult] = useState<TriageVisitResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const p = await getPatient(patientId);
        setPatient(p);
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

  async function handleSubmit(data: CreateVisitRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const res = await createTriageVisit(patientId, data);
      setResult(res);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Triage submission failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
      </div>
    );
  }

  if (!patient) {
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
        href={`/patients/${patient.id}`}
        className="inline-flex items-center gap-1.5 text-sm text-navy/60 hover:text-navy transition-colors"
      >
        <ArrowLeft size={16} />
        Back to patient
      </Link>

      <PatientHeaderCard patient={patient} />

      {!result ? (
        <>
          <div>
            <h2 className="text-lg font-semibold text-navy">
              New Triage Visit
            </h2>
            <p className="mt-1 text-sm text-navy/60">
              Enter the patient transcript or complaint below.
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <TriageVisitForm onSubmit={handleSubmit} loading={submitting} />
        </>
      ) : (
        <TriageResultCard
          result={result}
          patientId={patient.id}
          onNewVisit={() => setResult(null)}
        />
      )}
    </div>
  );
}
