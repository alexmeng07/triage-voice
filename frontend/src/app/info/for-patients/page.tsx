"use client";

import Link from "next/link";
import { ArrowLeft, Heart, Clock, ShieldCheck, Phone } from "lucide-react";

export default function ForPatientsPage() {
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
          Information for Patients
        </h1>
        <p className="mt-2 text-navy/60">
          We want to make sure you understand why we ask certain questions and
          how your information is used.
        </p>
      </div>

      <div className="space-y-6">
        <section className="rounded-xl border border-navy/10 bg-white p-6 space-y-3">
          <div className="flex items-center gap-2 text-navy">
            <Heart size={18} />
            <h2 className="font-semibold">Why are we asking you questions?</h2>
          </div>
          <p className="text-sm text-navy/70">
            When you arrive at the clinic, our reception team asks about your
            symptoms to help determine how quickly you need to be seen. This
            process is called <strong>triage</strong> — it helps ensure that
            patients with the most urgent needs are seen first.
          </p>
          <p className="text-sm text-navy/70">
            Your answers are recorded to help the clinical team understand your
            condition. A computer system may assist with organizing this
            information, but <strong>all medical decisions are always made by
            your healthcare providers</strong>, not by any computer system.
          </p>
        </section>

        <section className="rounded-xl border border-navy/10 bg-white p-6 space-y-3">
          <div className="flex items-center gap-2 text-navy">
            <Clock size={18} />
            <h2 className="font-semibold">What does my priority level mean?</h2>
          </div>
          <p className="text-sm text-navy/70">
            After the initial assessment, you may be assigned a priority level
            from 1 (most urgent) to 5 (least urgent). This helps the clinic
            manage the order in which patients are seen. A higher priority number
            does <strong>not</strong> mean your concerns are unimportant — it
            means that, based on the initial assessment, your condition may be
            safe to wait a little longer.
          </p>
          <p className="text-sm text-navy/70">
            Priority levels are suggestions and may be adjusted by clinical
            staff at any time based on their professional judgment.
          </p>
        </section>

        <section className="rounded-xl border border-navy/10 bg-white p-6 space-y-3">
          <div className="flex items-center gap-2 text-navy">
            <ShieldCheck size={18} />
            <h2 className="font-semibold">How is my information used?</h2>
          </div>
          <p className="text-sm text-navy/70">
            The information you provide is used solely for your care and for
            improving the quality of our triage process. It is stored securely
            and handled in accordance with your clinic&apos;s privacy policies.
          </p>
          <p className="text-sm text-navy/70">
            If you have questions about data privacy, please ask a staff member
            or refer to the clinic&apos;s privacy notice.
          </p>
        </section>

        <section className="rounded-xl border border-amber-200 bg-amber-50 p-6 space-y-3">
          <div className="flex items-center gap-2 text-amber-800">
            <Phone size={18} />
            <h2 className="font-semibold">If your symptoms get worse</h2>
          </div>
          <p className="text-sm text-amber-800">
            If your symptoms get worse while you are waiting, please tell a
            staff member <strong>immediately</strong>. Do not wait for your name
            to be called. Symptoms that should prompt immediate attention
            include:
          </p>
          <ul className="text-sm text-amber-800 list-disc list-inside space-y-1">
            <li>Difficulty breathing or feeling short of breath</li>
            <li>New or worsening chest pain</li>
            <li>Sudden weakness, numbness, or confusion</li>
            <li>Severe bleeding that won&apos;t stop</li>
            <li>Loss of consciousness or feeling faint</li>
            <li>Any other sudden change that concerns you</li>
          </ul>
          <p className="text-sm text-amber-800 font-medium">
            If you are experiencing a life-threatening emergency, call
            emergency services (e.g., 911) immediately.
          </p>
        </section>
      </div>

      <div className="text-center">
        <button
          onClick={() => window.print()}
          className="rounded-xl border border-navy/15 px-6 py-2.5 text-sm text-navy transition-colors hover:bg-navy/5 cursor-pointer"
        >
          Print this page
        </button>
      </div>
    </div>
  );
}
