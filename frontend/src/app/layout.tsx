import type { Metadata } from "next";
import { Lora } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const lora = Lora({
  variable: "--font-lora",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Triage Voice — Patient Intake",
  description: "Receptionist patient intake and triage workflow",
};

const appMode = process.env.NEXT_PUBLIC_APP_MODE || "development";

function ModeBanner() {
  if (appMode === "production" || appMode === "pilot") return null;
  const isTraining = appMode === "training";
  return (
    <div
      className={`text-center text-xs font-medium py-1.5 ${
        isTraining
          ? "bg-amber-100 text-amber-800 border-b border-amber-200"
          : "bg-sky/20 text-navy border-b border-sky/30"
      }`}
    >
      {isTraining
        ? "Training Sandbox — fake data only"
        : "Development Mode"}
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${lora.variable} font-serif antialiased flex flex-col min-h-screen`}>
        <ModeBanner />
        <header className="border-b border-navy/10 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link
              href="/"
              className="text-xl font-semibold text-navy tracking-tight"
            >
              Triage Voice
            </Link>
            <div className="flex items-center gap-6 text-sm">
              <Link
                href="/patients"
                className="text-navy/70 hover:text-navy transition-colors"
              >
                Find Patient
              </Link>
              <Link
                href="/patients/register"
                className="text-navy/70 hover:text-navy transition-colors"
              >
                Register
              </Link>
              <Link
                href="/queue"
                className="text-navy/70 hover:text-navy transition-colors"
              >
                Queue
              </Link>
              <Link
                href="/training/cases"
                className="text-navy/70 hover:text-navy transition-colors"
              >
                Training
              </Link>
            </div>
          </nav>
        </header>

        <main className="mx-auto max-w-5xl px-6 py-8 flex-1 w-full">{children}</main>

        <footer className="border-t border-navy/10 bg-white/60 py-4 mt-auto">
          <div className="mx-auto max-w-5xl px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-navy/40">
            <p>
              This is a training and documentation aid, not medical advice or a
              clinical decision support tool.{" "}
              <Link href="/info/esi" className="underline hover:text-navy/60 transition-colors">
                Learn about ESI levels
              </Link>
            </p>
            <div className="flex gap-4">
              <Link href="/info/esi" className="hover:text-navy/60 transition-colors">
                ESI Info
              </Link>
              <Link href="/info/for-patients" className="hover:text-navy/60 transition-colors">
                For Patients
              </Link>
              <Link href="/admin/stats" className="hover:text-navy/60 transition-colors">
                Analytics
              </Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
