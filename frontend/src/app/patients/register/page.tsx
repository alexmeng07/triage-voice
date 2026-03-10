"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerPatient, ApiError } from "@/lib/api";
import PatientRegistrationForm from "@/components/PatientRegistrationForm";
import type { CreatePatientRequest, PatientResponse } from "@/lib/types";
import { AlertTriangle, User } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<PatientResponse[]>([]);
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
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Possible duplicate patient(s) detected
              </p>
              <p className="text-sm text-amber-700 mt-1">
                The patient was created, but records with the same name and date
                of birth already exist. Please confirm this is not a duplicate
                per your clinic&apos;s policy.
              </p>
            </div>
          </div>

          <div className="space-y-2 ml-8">
            {duplicates.map((d) => (
              <Link
                key={d.id}
                href={`/patients/${d.id}`}
                className="flex items-center gap-3 rounded-lg border border-amber-200 bg-white px-4 py-3 text-sm transition-colors hover:border-amber-400 cursor-pointer"
              >
                <User size={16} className="text-amber-600 shrink-0" />
                <div className="flex-1 min-w-0">
                  <span className="font-medium text-navy">
                    {d.last_name}, {d.first_name}
                  </span>
                  <span className="text-navy/50 ml-2">
                    DOB: {d.date_of_birth}
                    {d.phone ? ` · ${d.phone}` : ""}
                  </span>
                </div>
                <span className="text-xs text-navy/30">ID #{d.id}</span>
              </Link>
            ))}
          </div>

          <div className="flex gap-3 ml-8">
            {createdPatientId && (
              <Link
                href={`/patients/${createdPatientId}`}
                className="rounded-lg bg-navy px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-navy-dark cursor-pointer"
              >
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
