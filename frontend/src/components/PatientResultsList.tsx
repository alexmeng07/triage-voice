import type { PatientResponse } from "@/lib/types";
import { User } from "lucide-react";

interface Props {
  patients: PatientResponse[];
  onSelect: (patient: PatientResponse) => void;
}

export default function PatientResultsList({ patients, onSelect }: Props) {
  if (patients.length === 0) {
    return (
      <div className="rounded-xl border border-navy/10 bg-white px-6 py-12 text-center">
        <p className="text-navy/40 text-sm">No patients found.</p>
        <p className="text-navy/30 text-xs mt-1">
          Try a different search or register a new patient.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-navy/40">
        {patients.length} {patients.length === 1 ? "result" : "results"}
      </p>
      <div className="space-y-2">
        {patients.map((p) => (
          <button
            key={p.id}
            onClick={() => onSelect(p)}
            className="w-full flex items-center gap-4 rounded-xl border border-navy/10 bg-white px-5 py-4 text-left transition-all hover:border-sky hover:shadow-sm cursor-pointer"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sky/15 text-navy">
              <User size={18} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-navy truncate">
                {p.last_name}, {p.first_name}
              </p>
              <p className="text-xs text-navy/50 mt-0.5">
                DOB: {p.date_of_birth}
                {p.phone ? ` · Phone: ${p.phone}` : ""}
                {p.sex ? ` · ${p.sex}` : ""}
              </p>
            </div>
            <span className="text-xs text-navy/30">ID&nbsp;#{p.id}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
