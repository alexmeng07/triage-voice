import Link from "next/link";
import { Search, UserPlus } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] gap-12">
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-semibold text-navy tracking-tight">
          Patient Intake
        </h1>
        <p className="text-lg text-navy/60 max-w-md">
          Search for an existing patient or register a new one to begin.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-lg">
        <Link
          href="/patients"
          className="group flex flex-col items-center gap-4 rounded-2xl border border-navy/10 bg-white p-8 text-center transition-all hover:border-sky hover:shadow-md cursor-pointer"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-sky/15 text-navy group-hover:bg-sky/25 transition-colors">
            <Search size={24} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-navy">Find Patient</h2>
            <p className="mt-1 text-sm text-navy/50">
              Search by name, DOB, or phone
            </p>
          </div>
        </Link>

        <Link
          href="/patients/register"
          className="group flex flex-col items-center gap-4 rounded-2xl border border-navy/10 bg-white p-8 text-center transition-all hover:border-sky hover:shadow-md cursor-pointer"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-sage/40 text-navy group-hover:bg-sage/60 transition-colors">
            <UserPlus size={24} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-navy">
              Register Patient
            </h2>
            <p className="mt-1 text-sm text-navy/50">
              Create a new patient record
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}
