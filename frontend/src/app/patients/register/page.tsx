"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerPatient, ApiError } from "@/lib/api";
import PatientRegistrationForm from "@/components/PatientRegistrationForm";
import type { CreatePatientRequest, FuzzyPatientMatch } from "@/lib/types";
import { AlertTriangle, User, CheckCircle2 } from "lucide-react";

const MATCH_LABELS: Record<string, string> = {
  exact_name_dob: "Exact match",
  exact_phone: "Phone match",
  fuzzy_name_dob: "Similar name + same DOB",
  fuzzy_name: "Similar name",
};

function DuplicateMatchBadge({ reason, score }: { reason: string; score: number }) {
  const isExact = score === 100;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium leading-none ${
        isExact
          ? "border-red-200 bg-red-50 text-red-700"
          : "border-amber-200 bg-amber-50 text-amber-700"
      }`}
    >
      {MATCH_LABELS[reason] ?? reason.replace(/_/g, " ")}
      {!isExact && <span className="opacity-60">{score}%</span>}
    </span>
  );
}

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<FuzzyPatientMatch[]>([]);
  const [createdPatientId, setCreatedPatientId] = useState<number | null>(null);

  async function handleSubmit(data: CreatePatientRequest) {
    setLoading(true);
    setError(null);
    setDuplicateWarning(null);
    setDuplicates([]);

    try {
      const result = await registerPatient(data);

      if (result.duplicate_warning && result.duplicates.length > 0) {
        setDuplicateWarning(result.duplicate_warning);
        setDuplicates(result.duplicates);
        setCreatedPatientId(result.patient.id);
        setLoading(false);
        return;
      }

      router.push(`/patients/${result.patient.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Registration failed");
      setLoading(false);
    }
  }

  const hasExactDupes = duplicates.some((d) => d.match_score === 100);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-navy">Register Patient</h1>
        <p className="mt-1 text-navy/60">
          Enter the patient&apos;s information below.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {duplicateWarning && (
        <div
          className={`rounded-xl border p-5 space-y-4 ${
            hasExactDupes
              ? "border-red-200 bg-red-50/50"
              : "border-amber-200 bg-amber-50"
          }`}
        >
          <div className="flex items-start gap-3">
            <AlertTriangle
              size={20}
              className={`shrink-0 mt-0.5 ${
                hasExactDupes ? "text-red-600" : "text-amber-600"
              }`}
            />
            <div>
              <p
                className={`text-sm font-medium ${
                  hasExactDupes ? "text-red-800" : "text-amber-800"
                }`}
              >
                {hasExactDupes
                  ? "Likely duplicate patient detected"
                  : "Possible similar patient(s) found"}
              </p>
              <p
                className={`text-sm mt-1 ${
                  hasExactDupes ? "text-red-700" : "text-amber-700"
                }`}
              >
                The patient was created, but existing records may represent the
                same person. Review the matches below and confirm per your
                clinic&apos;s policy.
              </p>
            </div>
          </div>

          <div className="space-y-2 ml-8">
            {duplicates.map((d) => (
              <Link
                key={d.id}
                href={`/patients/${d.id}`}
                className={`flex items-center gap-3 rounded-lg border bg-white px-4 py-3 text-sm transition-colors cursor-pointer ${
                  d.match_score === 100
                    ? "border-red-200 hover:border-red-400"
                    : "border-amber-200 hover:border-amber-400"
                }`}
              >
                <User
                  size={16}
                  className={`shrink-0 ${
                    d.match_score === 100 ? "text-red-600" : "text-amber-600"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-navy">
                      {d.last_name}, {d.first_name}
                    </span>
                    <DuplicateMatchBadge
                      reason={d.match_reason}
                      score={d.match_score}
                    />
                  </div>
                  <p className="text-xs text-navy/50 mt-0.5">
                    DOB: {d.date_of_birth}
                    {d.phone ? ` · ${d.phone}` : ""}
                  </p>
                </div>
                <span className="text-xs text-navy/30">ID #{d.id}</span>
              </Link>
            ))}
          </div>

          <div className="flex gap-3 ml-8">
            {createdPatientId && (
              <Link
                href={`/patients/${createdPatientId}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-navy px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-navy-dark cursor-pointer"
              >
                <CheckCircle2 size={14} />
                Go to newly created patient
              </Link>
            )}
          </div>
        </div>
      )}

      {!duplicateWarning && (
        <PatientRegistrationForm onSubmit={handleSubmit} loading={loading} />
      )}
    </div>
  );
}
