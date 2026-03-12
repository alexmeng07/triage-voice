/* TypeScript interfaces mirroring backend Pydantic models. */

// ── Response types ──────────────────────────────────────────────────────

export interface PatientResponse {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone: string | null;
  sex: string | null;
  address: string | null;
  created_at: string;
  updated_at: string;
}

export interface FuzzyPatientMatch extends PatientResponse {
  match_score: number;
  match_reason: string;
}

export interface PatientLookupResponse {
  matches: PatientResponse[];
  count: number;
}

export interface FuzzySearchResponse {
  matches: FuzzyPatientMatch[];
  count: number;
}

export interface RegisterPatientResponse {
  patient: PatientResponse;
  duplicate_warning: string | null;
  duplicates: FuzzyPatientMatch[];
}

export interface VisitResponse {
  id: number;
  patient_id: number;
  chief_complaint: string | null;
  triage_note: string | null;
  esi_level: number | null;
  triage_method: string | null;
  triage_summary: string | null;
  recommended_action: string | null;
  pain_score: number | null;
  onset: string | null;
  symptom_location: string | null;
  reviewed_by: string | null;
  reviewed_role: string | null;
  final_esi_level: number | null;
  disposition: string | null;
  status: string | null;
  arrival_time: string | null;
  triage_time: string | null;
  created_at: string;
}

export interface TriageResponse {
  esi_level: number;
  red_flags: string[];
  summary: string;
  recommended_action: string;
  confidence: number | null;
  method: string;
  disclaimer: string;
}

export interface TriageVisitResponse {
  visit: VisitResponse;
  triage: TriageResponse;
}

/** Response from POST /triage/audio — transcript + triage (no visit created). */
export interface AudioTriageResponse extends TriageResponse {
  transcript: string;
}

// ── Request types ───────────────────────────────────────────────────────

export interface CreatePatientRequest {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone?: string;
  sex?: string;
  address?: string;
}

export interface PatientLookupRequest {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  phone?: string;
}

export interface CreateVisitRequest {
  transcript_or_note: string;
  pain_score?: number | null;
  onset?: string | null;
  symptom_location?: string | null;
}

export interface VisitReviewRequest {
  reviewed_by?: string | null;
  reviewed_role?: string | null;
  final_esi_level?: number | null;
  disposition?: string | null;
}

// ── Training types ──────────────────────────────────────────────────────

export interface TrainingCase {
  id: number;
  title: string;
  description: string;
  transcript: string;
  target_esi: number;
  rationale: string | null;
  category: string | null;
  created_at: string;
  /** Engine ESI from the most recent attempt; null if never triaged */
  last_engine_esi?: number | null;
  /** 1 if last attempt matched, 0 if not; null if never triaged */
  last_matched?: number | null;
}

export interface TriageAllResult {
  case_id: number;
  title: string;
  target_esi: number;
  engine_esi: number;
  matched: number;
}

export interface TriageAllResponse {
  results: TriageAllResult[];
  total: number;
  matched: number;
}

export interface TrainingAttemptResult {
  attempt: {
    id: number;
    case_id: number;
    engine_esi: number;
    expected_esi: number;
    matched: number;
    created_at: string;
  };
  triage: TriageResponse;
  expected_esi: number;
  matched: number;
}

export interface TrainingStats {
  case_id: number;
  title: string;
  target_esi: number;
  attempts: number;
  matches: number;
}

// ── Queue types (visit-centric) ──────────────────────────────────────────

export interface QueueVisitEntry {
  visit_id: number;
  patient_id: number;
  patient_name: string;
  date_of_birth: string;
  chief_complaint: string | null;
  esi_level: number | null;
  status: string;
  arrival_time: string | null;
  triage_time: string | null;
  wait_minutes: number | null;
}

export interface QueueSummary {
  waiting: number;
  in_triage: number;
  triaged: number;
  with_doctor: number;
}

/** @deprecated Use QueueVisitEntry and getQueue() for visit-centric queue. */
export interface QueueEntry {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone: string | null;
  sex: string | null;
  latest_visit_id: number | null;
  latest_esi_level: number | null;
  latest_triage_method: string | null;
  latest_chief_complaint: string | null;
  latest_visit_at: string | null;
  latest_final_esi: number | null;
  latest_disposition: string | null;
}

// ── Admin types ─────────────────────────────────────────────────────────

export interface EsiDistribution {
  esi_level: number | null;
  count: number;
}

export interface ComplaintCount {
  chief_complaint: string;
  count: number;
}

export interface AuditEntry {
  id: number;
  action_type: string;
  patient_id: number | null;
  visit_id: number | null;
  metadata: string | null;
  created_at: string;
}
