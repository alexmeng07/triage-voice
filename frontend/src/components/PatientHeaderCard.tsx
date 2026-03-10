import type { PatientResponse } from "@/lib/types";
import { User, Phone, MapPin, Calendar } from "lucide-react";

interface Props {
  patient: PatientResponse;
}

export default function PatientHeaderCard({ patient }: Props) {
  const sexLabel =
    patient.sex === "M"
      ? "Male"
      : patient.sex === "F"
        ? "Female"
        : patient.sex === "O"
          ? "Other"
          : null;

  return (
    <div className="rounded-xl border border-navy/10 bg-white p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-sky/15 text-navy">
          <User size={22} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-semibold text-navy">
            {patient.first_name} {patient.last_name}
          </h2>
          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-navy/60">
            <span className="inline-flex items-center gap-1.5">
              <Calendar size={14} className="shrink-0" />
              {patient.date_of_birth}
            </span>
            {patient.phone && (
              <span className="inline-flex items-center gap-1.5">
                <Phone size={14} className="shrink-0" />
                {patient.phone}
              </span>
            )}
            {sexLabel && <span>{sexLabel}</span>}
            {patient.address && (
              <span className="inline-flex items-center gap-1.5">
                <MapPin size={14} className="shrink-0" />
                {patient.address}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-navy/30">ID&nbsp;#{patient.id}</p>
        </div>
      </div>
    </div>
  );
}
