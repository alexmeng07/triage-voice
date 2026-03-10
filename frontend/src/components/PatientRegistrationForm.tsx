"use client";

import { useState } from "react";
import type { CreatePatientRequest } from "@/lib/types";

interface Props {
  onSubmit: (data: CreatePatientRequest) => void;
  loading: boolean;
}

export default function PatientRegistrationForm({ onSubmit, loading }: Props) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [phone, setPhone] = useState("");
  const [sex, setSex] = useState("");
  const [address, setAddress] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!firstName.trim()) next.first_name = "First name is required";
    if (!lastName.trim()) next.last_name = "Last name is required";
    if (!dob) next.date_of_birth = "Date of birth is required";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    const data: CreatePatientRequest = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      date_of_birth: dob,
    };
    if (phone.trim()) data.phone = phone.trim();
    if (sex) data.sex = sex;
    if (address.trim()) data.address = address.trim();

    onSubmit(data);
  }

  const fieldClass =
    "w-full rounded-lg border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-sky focus:ring-2 focus:ring-sky/20";

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-navy/10 bg-white p-6 space-y-5"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            First Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            className={fieldClass}
          />
          {errors.first_name && (
            <p className="text-xs text-red-500 mt-1">{errors.first_name}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Last Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className={fieldClass}
          />
          {errors.last_name && (
            <p className="text-xs text-red-500 mt-1">{errors.last_name}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Date of Birth <span className="text-red-400">*</span>
          </label>
          <input
            type="date"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            className={fieldClass}
          />
          {errors.date_of_birth && (
            <p className="text-xs text-red-500 mt-1">{errors.date_of_birth}</p>
          )}
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
            className={`${fieldClass} placeholder:text-navy/30`}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Sex
          </label>
          <select
            value={sex}
            onChange={(e) => setSex(e.target.value)}
            className={fieldClass}
          >
            <option value="">—</option>
            <option value="M">Male</option>
            <option value="F">Female</option>
            <option value="O">Other</option>
          </select>
        </div>

        <div className="sm:col-span-2">
          <label className="block text-xs font-medium text-navy/60 mb-1">
            Address
          </label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="123 Main St, Anytown, USA"
            className={`${fieldClass} placeholder:text-navy/30`}
          />
        </div>
      </div>

      <div className="rounded-lg border border-navy/10 bg-cream px-4 py-3 text-xs text-navy/50 space-y-1">
        <p>
          By registering this patient, you acknowledge that their information
          may be processed by an automated triage support system for
          documentation and training purposes.
        </p>
        <p>
          All clinical decisions remain the responsibility of qualified
          healthcare professionals. This tool is not medical advice.
        </p>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="rounded-xl bg-navy px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-dark disabled:opacity-40 cursor-pointer"
      >
        {loading ? "Registering\u2026" : "Register Patient"}
      </button>
    </form>
  );
}
