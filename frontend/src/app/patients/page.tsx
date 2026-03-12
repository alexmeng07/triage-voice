"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { searchPatients, lookupPatients, ApiError } from "@/lib/api";
import type {
  PatientResponse,
  FuzzyPatientMatch,
  PatientLookupRequest,
} from "@/lib/types";
import PatientSearchForm from "@/components/PatientSearchForm";
import PatientResultsList from "@/components/PatientResultsList";

export default function PatientsPage() {
  const router = useRouter();
  const [results, setResults] = useState<FuzzyPatientMatch[] | null>(null);
  const [exactResults, setExactResults] = useState<PatientResponse[] | null>(
    null,
  );
  const [searchMode, setSearchMode] = useState<"fuzzy" | "advanced">("fuzzy");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleQuickSearch(query: string) {
    setLoading(true);
    setError(null);
    setExactResults(null);
    setSearchMode("fuzzy");
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
    setResults(null);
    setSearchMode("advanced");
    try {
      const data = await lookupPatients(payload);
      setExactResults(data.matches);
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
          Search by name, date of birth, or phone. Fuzzy matching finds close
          spellings.
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

      {searchMode === "fuzzy" && results !== null && (
        <PatientResultsList
          patients={results}
          onSelect={handleSelectPatient}
          showMatchQuality
        />
      )}

      {searchMode === "advanced" && exactResults !== null && (
        <PatientResultsList
          patients={exactResults}
          onSelect={handleSelectPatient}
        />
      )}
    </div>
  );
}
