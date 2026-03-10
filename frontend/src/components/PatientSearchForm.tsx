"use client";

import { useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import type { PatientLookupRequest } from "@/lib/types";

interface Props {
  onQuickSearch: (query: string) => void;
  onAdvancedLookup: (payload: PatientLookupRequest) => void;
  loading: boolean;
}

export default function PatientSearchForm({
  onQuickSearch,
  onAdvancedLookup,
  loading,
}: Props) {
  const [query, setQuery] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [phone, setPhone] = useState("");

  function handleQuickSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) onQuickSearch(query.trim());
  }

  function handleAdvancedSearch(e: React.FormEvent) {
    e.preventDefault();
    const payload: PatientLookupRequest = {};
    if (firstName.trim()) payload.first_name = firstName.trim();
    if (lastName.trim()) payload.last_name = lastName.trim();
    if (dob.trim()) payload.date_of_birth = dob.trim();
    if (phone.trim()) payload.phone = phone.trim();
    if (Object.keys(payload).length > 0) onAdvancedLookup(payload);
  }

  const advancedHasInput =
    firstName.trim() || lastName.trim() || dob.trim() || phone.trim();

  return (
    <div className="space-y-4">
      <form onSubmit={handleQuickSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search
            size={18}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-navy/30 pointer-events-none"
          />
          <input
            type="text"
            placeholder="Search by name or phone..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-xl border border-navy/15 bg-white py-2.5 pl-10 pr-4 text-sm outline-none transition-colors focus:border-sky focus:ring-2 focus:ring-sky/20 placeholder:text-navy/30"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded-xl bg-navy px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-dark disabled:opacity-40 cursor-pointer"
        >
          {loading ? "Searching\u2026" : "Search"}
        </button>
      </form>

      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="inline-flex items-center gap-1.5 text-sm text-navy/50 hover:text-navy transition-colors cursor-pointer"
      >
        <SlidersHorizontal size={14} />
        {showAdvanced ? "Hide advanced lookup" : "Advanced lookup"}
      </button>

      {showAdvanced && (
        <form
          onSubmit={handleAdvancedSearch}
          className="rounded-xl border border-navy/10 bg-white p-5 space-y-4"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-navy/60 mb-1">
                First Name
              </label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-navy/60 mb-1">
                Last Name
              </label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-navy/60 mb-1">
                Date of Birth
              </label>
              <input
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-navy/60 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="555-123-4567"
                className="w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20 placeholder:text-navy/30"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !advancedHasInput}
            className="rounded-xl bg-navy px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-dark disabled:opacity-40 cursor-pointer"
          >
            {loading ? "Searching\u2026" : "Look Up"}
          </button>
        </form>
      )}
    </div>
  );
}
