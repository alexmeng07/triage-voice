import Link from "next/link";
import { ArrowLeft, ShieldAlert, AlertTriangle, Clock, Stethoscope, HeartPulse } from "lucide-react";

const ESI_LEVELS = [
  {
    level: 1,
    name: "Resuscitation",
    description:
      "Immediate life-saving intervention required. The patient is not breathing, has no pulse, or is in cardiac arrest.",
    color: "bg-red-100 text-red-800 border-red-200",
    icon: HeartPulse,
  },
  {
    level: 2,
    name: "Emergent",
    description:
      "High-risk situation with altered mental status, severe pain/distress, or symptoms suggesting stroke, heart attack, or other time-critical conditions.",
    color: "bg-orange-100 text-orange-800 border-orange-200",
    icon: ShieldAlert,
  },
  {
    level: 3,
    name: "Urgent",
    description:
      "The patient likely needs multiple resources (labs, imaging, IV fluids) but is not in immediate danger. Examples include abdominal pain with fever, or moderate injuries.",
    color: "bg-amber-100 text-amber-800 border-amber-200",
    icon: AlertTriangle,
  },
  {
    level: 4,
    name: "Less Urgent",
    description:
      "The patient likely needs one resource (e.g., an X-ray or sutures). Examples include a simple laceration or sprained ankle.",
    color: "bg-emerald-100 text-emerald-800 border-emerald-200",
    icon: Stethoscope,
  },
  {
    level: 5,
    name: "Non-Urgent",
    description:
      "The patient needs no resources beyond a brief exam. Examples include prescription refills, mild cold symptoms, or minor rashes.",
    color: "bg-sky/20 text-navy border-sky/30",
    icon: Clock,
  },
];

export default function EsiInfoPage() {
  return (
    <div className="space-y-8 max-w-3xl">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-navy/60 hover:text-navy transition-colors"
      >
        <ArrowLeft size={16} />
        Back to home
      </Link>

      <div>
        <h1 className="text-2xl font-semibold text-navy">
          Understanding ESI Triage Levels
        </h1>
        <p className="mt-2 text-navy/60">
          The Emergency Severity Index (ESI) is a five-level triage system used
          in emergency departments to prioritize patients based on the urgency of
          their condition and expected resource needs. Lower numbers indicate
          higher urgency.
        </p>
      </div>

      <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
        <p className="font-medium">Important</p>
        <p className="mt-1">
          This application provides ESI level <em>suggestions</em> for training
          and documentation purposes only. The suggested level must always be
          reviewed and confirmed by a qualified clinician before any clinical
          decisions are made. This tool is not a clinical decision support system.
        </p>
      </div>

      <div className="space-y-4">
        {ESI_LEVELS.map((esi) => {
          const Icon = esi.icon;
          return (
            <div
              key={esi.level}
              className={`rounded-xl border px-5 py-4 ${esi.color}`}
            >
              <div className="flex items-start gap-3">
                <Icon size={20} className="shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold">
                    ESI {esi.level} — {esi.name}
                  </h3>
                  <p className="mt-1 text-sm opacity-80">{esi.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-xs text-navy/40">
        <p>
          Reference: Gilboy N, Tanabe T, Travers D, Rosenau AM. Emergency
          Severity Index (ESI): A Triage Tool for Emergency Department Care,
          Version 4. AHRQ Publication No. 12-0014. Rockville, MD: Agency for
          Healthcare Research and Quality; 2011.
        </p>
      </div>
    </div>
  );
}
