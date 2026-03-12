import type {
  PatientLookupResponse,
  FuzzySearchResponse,
  PatientLookupRequest,
  PatientResponse,
  RegisterPatientResponse,
  CreatePatientRequest,
  VisitResponse,
  TriageVisitResponse,
  CreateVisitRequest,
  VisitReviewRequest,
  AudioTriageResponse,
  TrainingCase,
  TrainingAttemptResult,
  TrainingStats,
  TriageAllResponse,
  QueueEntry,
  QueueVisitEntry,
  QueueSummary,
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

export async function searchPatients(q: string): Promise<FuzzySearchResponse> {
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

/**
 * Triage from audio file (transcript + triage only, no visit).
 * Use createTriageVisitFromAudio when on a patient page to save as visit.
 */
export async function triageAudio(file: File): Promise<AudioTriageResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/triage/audio`,
    {
      method: "POST",
      body: formData,
      headers: {}, // do not set Content-Type — browser sets multipart boundary
    },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ?? res.statusText);
  }
  return res.json();
}

/**
 * Upload audio for triage and create a visit for the patient in one request.
 */
export async function createTriageVisitFromAudio(
  patientId: number,
  file: File,
): Promise<TriageVisitResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/patients/${patientId}/triage-audio-visit`,
    {
      method: "POST",
      body: formData,
      headers: {},
    },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ?? res.statusText);
  }
  return res.json();
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

// ── Queue (visit-centric) ────────────────────────────────────────────────

export async function getQueue(): Promise<QueueVisitEntry[]> {
  return request("/queue");
}

export async function getQueueSummary(): Promise<QueueSummary> {
  return request("/queue/summary");
}

export async function updateVisitStatus(
  visitId: number,
  status: string,
): Promise<VisitResponse> {
  return request(`/visits/${visitId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

/** @deprecated Use getQueue() for visit-centric queue. */
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

export async function triageAllCases(): Promise<TriageAllResponse> {
  return request("/training/cases/triage-all", { method: "POST" });
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
