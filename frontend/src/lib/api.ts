import type {
  PatientLookupResponse,
  PatientLookupRequest,
  PatientResponse,
  RegisterPatientResponse,
  CreatePatientRequest,
  VisitResponse,
  TriageVisitResponse,
  CreateVisitRequest,
  VisitReviewRequest,
  TrainingCase,
  TrainingAttemptResult,
  TrainingStats,
  QueueEntry,
  EsiDistribution,
  ComplaintCount,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ?? res.statusText);
  }

  return res.json();
}

// ── Patient endpoints ───────────────────────────────────────────────────

export async function searchPatients(q: string): Promise<PatientLookupResponse> {
  return request(`/patients/search?q=${encodeURIComponent(q)}`);
}

export async function lookupPatients(
  payload: PatientLookupRequest,
): Promise<PatientLookupResponse> {
  return request("/patients/lookup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function registerPatient(
  payload: CreatePatientRequest,
): Promise<RegisterPatientResponse> {
  return request("/patients/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPatient(id: number): Promise<PatientResponse> {
  return request(`/patients/${id}`);
}

export async function getPatientVisits(id: number): Promise<VisitResponse[]> {
  return request(`/patients/${id}/visits`);
}

export async function createTriageVisit(
  patientId: number,
  payload: CreateVisitRequest,
): Promise<TriageVisitResponse> {
  return request(`/patients/${patientId}/triage-visit`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Visit review ────────────────────────────────────────────────────────

export async function reviewVisit(
  visitId: number,
  payload: VisitReviewRequest,
): Promise<VisitResponse> {
  return request(`/visits/${visitId}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// ── Queue ───────────────────────────────────────────────────────────────

export async function getPatientQueue(): Promise<QueueEntry[]> {
  return request("/patients/queue");
}

// ── Training ────────────────────────────────────────────────────────────

export async function getTrainingCases(): Promise<TrainingCase[]> {
  return request("/training/cases");
}

export async function getTrainingCase(id: number): Promise<TrainingCase> {
  return request(`/training/cases/${id}`);
}

export async function attemptTrainingCase(caseId: number): Promise<TrainingAttemptResult> {
  return request(`/training/cases/${caseId}/attempt`, { method: "POST" });
}

export async function getTrainingStats(): Promise<TrainingStats[]> {
  return request("/training/stats");
}

// ── Admin / Analytics ───────────────────────────────────────────────────

export async function getEsiDistribution(since?: string): Promise<EsiDistribution[]> {
  const qs = since ? `?since=${encodeURIComponent(since)}` : "";
  return request(`/admin/stats/esi-distribution${qs}`);
}

export async function getCommonComplaints(limit = 10): Promise<ComplaintCount[]> {
  return request(`/admin/stats/common-complaints?limit=${limit}`);
}
