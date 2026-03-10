"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { searchPatients, lookupPatients, ApiError } from "@/lib/api";
import type { PatientResponse, PatientLookupRequest } from "@/lib/types";
import PatientSearchForm from "@/components/PatientSearchForm";
import PatientResultsList from "@/components/PatientResultsList";

export default function PatientsPage() {
  const router = useRouter();
  const [results, setResults] = useState<PatientResponse[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleQuickSearch(query: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await searchPatients(query);
      setResults(data.matches);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleAdvancedLookup(payload: PatientLookupRequest) {
    setLoading(true);
    setError(null);
    try {
      const data = await lookupPatients(payload);
      setResults(data.matches);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Lookup failed");
    } finally {
      setLoading(false);
    }
  }

  function handleSelectPatient(patient: PatientResponse) {
    router.push(`/patients/${patient.id}`);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-navy">Find Patient</h1>
        <p className="mt-1 text-navy/60">
          Search by name, date of birth, or phone number.
        </p>
      </div>

      <PatientSearchForm
        onQuickSearch={handleQuickSearch}
        onAdvancedLookup={handleAdvancedLookup}
        loading={loading}
      />

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {results !== null && (
        <PatientResultsList
          patients={results}
          onSelect={handleSelectPatient}
        />
      )}
    </div>
  );
}
