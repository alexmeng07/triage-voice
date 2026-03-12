import type { PatientResponse, FuzzyPatientMatch } from "@/lib/types";
import { User } from "lucide-react";

interface Props {
  patients: (PatientResponse | FuzzyPatientMatch)[];
  onSelect: (patient: PatientResponse) => void;
  showMatchQuality?: boolean;
}

const REASON_LABELS: Record<string, { label: string; className: string }> = {
  exact_name: {
    label: "Exact name",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  exact_name_dob: {
    label: "Exact match",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  exact_phone: {
    label: "Phone match",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  exact_last_name: {
    label: "Last name match",
    className: "border-sky/30 bg-sky/10 text-navy/70",
  },
  exact_first_name: {
    label: "First name match",
    className: "border-sky/30 bg-sky/10 text-navy/70",
  },
  strong_name_match: {
    label: "Strong match",
    className: "border-sky/30 bg-sky/10 text-navy/70",
  },
  fuzzy_name: {
    label: "Similar name",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  },
  fuzzy_name_dob: {
    label: "Similar name + DOB",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  },
  substring: {
    label: "Partial match",
    className: "border-navy/10 bg-navy/5 text-navy/50",
  },
};

function MatchBadge({ reason, score }: { reason: string; score: number }) {
  const config = REASON_LABELS[reason] ?? {
    label: reason.replace(/_/g, " "),
    className: "border-navy/10 bg-navy/5 text-navy/50",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium leading-none ${config.className}`}
    >
      {config.label}
      {score < 100 && (
        <span className="opacity-60">{score}%</span>
      )}
    </span>
  );
}

function isFuzzy(p: PatientResponse | FuzzyPatientMatch): p is FuzzyPatientMatch {
  return "match_score" in p && typeof p.match_score === "number";
}

export default function PatientResultsList({
  patients,
  onSelect,
  showMatchQuality = false,
}: Props) {
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
              <div className="flex items-center gap-2">
                <p className="font-medium text-navy truncate">
                  {p.last_name}, {p.first_name}
                </p>
                {showMatchQuality && isFuzzy(p) && (
                  <MatchBadge reason={p.match_reason} score={p.match_score} />
                )}
              </div>
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
