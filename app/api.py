"""FastAPI application — HTTP layer over the triage pipeline.

Includes:
- Original triage endpoints (/health, /ready, /triage, /triage/audio, /version)
- Patient registration, lookup, and visit endpoints (new)
"""

from __future__ import annotations

import logging
import os
import subprocess
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Existing triage imports
from app.api_schemas import (
    AudioTriageResponse,
    HealthResponse,
    ReadyResponse,
    TriageRequest,
    TriageResponse,
    VersionResponse,
)
from app.stt import transcribe_wav_bytes
from app.triage_engine import triage

# New patient imports
from app.database import init_db
from app.patient_repository import (
    check_duplicate_patient,
    check_fuzzy_duplicates,
    create_audit_entry,
    create_patient,
    create_training_attempt,
    create_visit,
    get_common_complaints,
    get_esi_distribution,
    get_patient_by_id,
    get_queue_summary,
    get_training_case_by_id,
    get_training_stats,
    get_visit_by_id,
    list_active_queue_visits,
    list_audit_entries,
    list_todays_patients_with_visits,
    list_training_cases,
    list_training_cases_with_attempts,
    list_visits_for_patient,
    lookup_patients,
    search_patients,
    search_patients_fuzzy,
    update_visit_review,
    update_visit_status,
)
from app.patient_schemas import (
    CreatePatientRequest,
    CreateVisitRequest,
    FuzzyPatientMatch,
    FuzzySearchResponse,
    PatientLookupRequest,
    PatientLookupResponse,
    PatientResponse,
    QueueVisitResponse,
    RegisterPatientResponse,
    TriageVisitResponse,
    VisitReviewRequest,
    VisitResponse,
    VisitStatusUpdateRequest,
)

load_dotenv()

logger = logging.getLogger(__name__)

APP_VERSION = "0.1.0"

ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/webm;codecs=opus,vorbis",
    "audio/flac",
    "audio/mp4",
    "audio/x-m4a",
}


def _is_allowed_audio_type(content_type: str | None) -> bool:
    """Accept exact matches and variants like audio/webm;codecs=opus (with/without space)."""
    if not content_type:
        return True
    ct = content_type.strip().split(";")[0].strip().lower()
    if content_type in ALLOWED_AUDIO_TYPES:
        return True
    # Accept audio/webm* and audio/mp4* (codec params vary by browser)
    if ct in ("audio/webm", "audio/mp4") or content_type.lower().startswith(
        ("audio/webm", "audio/mp4")
    ):
        return True
    return False

# ---------------------------------------------------------------------------
# Lifespan — runs once on startup/shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the SQLite database when the server starts."""
    init_db()
    logger.info("Patient database ready.")
    yield  # app runs here
    # Nothing special to clean up on shutdown (SQLite handles itself).


# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(
    title="triage-voice",
    version=APP_VERSION,
    description="ESI triage simulation API (not medical advice).",
    lifespan=lifespan,
)

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================================================
#  EXISTING ROUTES — unchanged
# ===========================================================================


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    from app.ml_model import ESIClassifier

    try:
        clf = ESIClassifier()
        clf._load()
        return ReadyResponse(ml_ready=True, mode="ml")
    except FileNotFoundError:
        return ReadyResponse(
            ml_ready=False,
            mode="rule_fallback",
            message="Run `python -m training.train_esi345` to generate artifacts.",
        )


@app.post("/triage", response_model=TriageResponse)
async def triage_text(req: TriageRequest) -> TriageResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must not be blank")

    result = triage(text)
    return TriageResponse(**result.to_dict())


@app.post("/triage/audio", response_model=AudioTriageResponse)
async def triage_audio(file: UploadFile) -> AudioTriageResponse:
    if not _is_allowed_audio_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{file.content_type}'. Expected audio file.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        transcript = transcribe_wav_bytes(data, filename=file.filename or "upload.wav")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"STT failed: {exc}") from exc

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=422, detail="STT returned empty transcript — audio may be silent or unrecognizable"
        )

    result = triage(transcript)
    return AudioTriageResponse(**result.to_dict(), transcript=transcript)


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    git_commit: str | None = None
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            git_commit = proc.stdout.strip() or None
    except Exception:
        pass
    return VersionResponse(version=APP_VERSION, git_commit=git_commit)


# ===========================================================================
#  PATIENT ROUTES — new
# ===========================================================================

# NOTE: The /patients/search route is defined BEFORE /patients/{patient_id}
# so FastAPI doesn't try to treat "search" as a patient_id integer.


@app.get("/patients/search", response_model=FuzzySearchResponse)
async def patient_search(
    q: str = Query(..., min_length=1, description="Free-text search for patients"),
) -> FuzzySearchResponse:
    """Search patients with fuzzy name matching and ranked results.

    Returns matches with match_score (0-100) and match_reason indicating
    how the result was matched (exact_name, exact_phone, fuzzy_name, etc).
    """
    matches = search_patients_fuzzy(q)
    return FuzzySearchResponse(
        matches=[FuzzyPatientMatch(**m) for m in matches],
        count=len(matches),
    )


@app.post("/patients/register", response_model=RegisterPatientResponse)
async def register_patient(req: CreatePatientRequest) -> RegisterPatientResponse:
    """Create a new patient record.

    Uses fuzzy matching to detect potential duplicates.  If any are found,
    a duplicate_warning is included along with scored match candidates
    (but the patient is still created — this is just an informational heads-up).
    """
    dupes = check_fuzzy_duplicates(
        req.first_name, req.last_name, req.date_of_birth, req.phone,
    )
    warning: str | None = None
    dupe_records: list[FuzzyPatientMatch] = []
    if dupes:
        exact = [d for d in dupes if d.get("match_score", 0) == 100]
        fuzzy = [d for d in dupes if d.get("match_score", 0) < 100]
        parts = []
        if exact:
            parts.append(f"{len(exact)} exact match(es)")
        if fuzzy:
            parts.append(f"{len(fuzzy)} similar record(s)")
        warning = f"Possible duplicate(s) found: {' and '.join(parts)}. Patient was still created."
        dupe_records = [FuzzyPatientMatch(**d) for d in dupes]

    patient = create_patient(
        first_name=req.first_name,
        last_name=req.last_name,
        date_of_birth=req.date_of_birth,
        phone=req.phone,
        sex=req.sex,
        address=req.address,
    )

    create_audit_entry("patient_registered", patient_id=patient["id"])

    return RegisterPatientResponse(
        patient=PatientResponse(**patient),
        duplicate_warning=warning,
        duplicates=dupe_records,
    )


@app.post("/patients/lookup", response_model=PatientLookupResponse)
async def patient_lookup(req: PatientLookupRequest) -> PatientLookupResponse:
    """Search for patients by combinations of identifying fields.

    At least one search field must be provided, otherwise returns HTTP 400.
    All provided fields are AND-ed together.
    """
    # Make sure the caller gave us at least one field to search on.
    has_any = any([req.first_name, req.last_name, req.date_of_birth, req.phone])
    if not has_any:
        raise HTTPException(
            status_code=400,
            detail="At least one search field (first_name, last_name, date_of_birth, phone) is required.",
        )

    matches = lookup_patients(
        first_name=req.first_name,
        last_name=req.last_name,
        date_of_birth=req.date_of_birth,
        phone=req.phone,
    )

    return PatientLookupResponse(
        matches=[PatientResponse(**m) for m in matches],
        count=len(matches),
    )


@app.get("/patients/queue")
async def patient_queue():
    """Return today's patients with their latest visit info (legacy, patient-centric)."""
    return list_todays_patients_with_visits()


# ---------------------------------------------------------------------------
# QUEUE (visit-centric)
# ---------------------------------------------------------------------------


@app.get("/queue", response_model=list[QueueVisitResponse])
async def get_queue() -> list[QueueVisitResponse]:
    """Return active visits (status != complete), sorted by acuity then arrival."""
    rows = list_active_queue_visits()
    return [QueueVisitResponse(
        visit_id=r["visit_id"],
        patient_id=r["patient_id"],
        patient_name=r["patient_name"],
        date_of_birth=r["date_of_birth"],
        chief_complaint=r.get("chief_complaint"),
        esi_level=r.get("esi_level"),
        status=r["status"],
        arrival_time=r.get("arrival_time"),
        triage_time=r.get("triage_time"),
        wait_minutes=r.get("wait_minutes"),
    ) for r in rows]


@app.get("/queue/summary")
async def get_queue_summary_route():
    """Return aggregate counts: waiting, in_triage, triaged, with_doctor."""
    return get_queue_summary()


@app.patch("/visits/{visit_id}/status", response_model=VisitResponse)
async def update_visit_status_route(
    visit_id: int,
    req: VisitStatusUpdateRequest,
) -> VisitResponse:
    """Update a visit's queue status."""
    updated = update_visit_status(visit_id, req.status)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Visit {visit_id} not found")
    create_audit_entry(
        "visit_status_updated",
        patient_id=updated["patient_id"],
        visit_id=visit_id,
        metadata=req.status,
    )
    return VisitResponse(**updated)


@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int) -> PatientResponse:
    """Retrieve a single patient by ID.  Returns 404 if not found."""
    patient = get_patient_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return PatientResponse(**patient)


@app.get("/patients/{patient_id}/visits", response_model=list[VisitResponse])
async def get_patient_visits(patient_id: int) -> list[VisitResponse]:
    """List all visits for a patient, newest first.

    Returns 404 if the patient doesn't exist.
    """
    # Make sure the patient exists before listing visits.
    patient = get_patient_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    visits = list_visits_for_patient(patient_id)
    return [VisitResponse(**v) for v in visits]


@app.post("/patients/{patient_id}/triage-visit", response_model=TriageVisitResponse)
async def create_triage_visit(patient_id: int, req: CreateVisitRequest) -> TriageVisitResponse:
    """Run the triage pipeline and record a visit for an existing patient.

    Flow:
    1. Confirm the patient exists (404 if not).
    2. Run the existing triage engine on the provided transcript/note.
    3. Store a new visit row with the triage results.
    4. Return both the visit record and triage output.
    """
    # Step 1: confirm patient exists
    patient = get_patient_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    triage_result = triage(req.transcript_or_note)

    visit = create_visit(
        patient_id=patient_id,
        chief_complaint=req.transcript_or_note,
        triage_note=req.transcript_or_note,
        esi_level=triage_result.esi_level,
        triage_method=triage_result.method,
        triage_summary=triage_result.summary,
        recommended_action=triage_result.recommended_action,
        pain_score=req.pain_score,
        onset=req.onset,
        symptom_location=req.symptom_location,
    )

    create_audit_entry("triage_visit_created", patient_id=patient_id, visit_id=visit["id"])

    return TriageVisitResponse(
        visit=VisitResponse(**visit),
        triage=TriageResponse(**triage_result.to_dict()),
    )


@app.post("/patients/{patient_id}/triage-audio-visit", response_model=TriageVisitResponse)
async def create_triage_visit_from_audio(
    patient_id: int,
    file: UploadFile,
) -> TriageVisitResponse:
    """Record a triage visit from an audio upload for an existing patient.

    Flow:
    1. Confirm the patient exists.
    2. Transcribe the audio via speech-to-text.
    3. Run the triage engine on the transcript.
    4. Store a new visit with the triage results.
    5. Return the visit record and triage output.
    """
    patient = get_patient_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    if not _is_allowed_audio_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{file.content_type}'. Expected audio file.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        transcript = transcribe_wav_bytes(data, filename=file.filename or "upload.wav")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"STT failed: {exc}") from exc

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=422,
            detail="STT returned empty transcript — audio may be silent or unrecognizable",
        )

    triage_result = triage(transcript)
    visit = create_visit(
        patient_id=patient_id,
        chief_complaint=transcript,
        triage_note=transcript,
        esi_level=triage_result.esi_level,
        triage_method=triage_result.method,
        triage_summary=triage_result.summary,
        recommended_action=triage_result.recommended_action,
    )

    create_audit_entry(
        "triage_visit_created",
        patient_id=patient_id,
        visit_id=visit["id"],
        metadata="audio",
    )

    return TriageVisitResponse(
        visit=VisitResponse(**visit),
        triage=TriageResponse(**triage_result.to_dict()),
    )


# ===========================================================================
#  VISIT REVIEW — clinician sign-off
# ===========================================================================


@app.patch("/visits/{visit_id}/review", response_model=VisitResponse)
async def review_visit(visit_id: int, req: VisitReviewRequest) -> VisitResponse:
    """Update clinician review fields on a visit."""
    existing = get_visit_by_id(visit_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Visit {visit_id} not found")

    updated = update_visit_review(
        visit_id=visit_id,
        reviewed_by=req.reviewed_by,
        reviewed_role=req.reviewed_role,
        final_esi_level=req.final_esi_level,
        disposition=req.disposition,
    )
    if updated is None:
        raise HTTPException(status_code=500, detail="Failed to update visit")

    create_audit_entry(
        "visit_reviewed",
        patient_id=existing["patient_id"],
        visit_id=visit_id,
    )

    return VisitResponse(**updated)


# ===========================================================================
#  TRAINING CASES
# ===========================================================================


@app.get("/training/cases")
async def list_cases():
    """List all training cases with latest attempt (engine_esi, matched) per case."""
    return list_training_cases_with_attempts()


@app.post("/training/cases/triage-all")
async def triage_all_cases():
    """Run triage on every training case, record attempts, and return results."""
    cases = list_training_cases()
    if not cases:
        return {"results": [], "total": 0, "matched": 0}
    results = []
    matched_count = 0
    for case in cases:
        triage_result = triage(case["transcript"])
        attempt = create_training_attempt(
            case_id=case["id"],
            engine_esi=triage_result.esi_level,
            expected_esi=case["target_esi"],
        )
        matched_count += attempt["matched"]
        results.append({
            "case_id": case["id"],
            "title": case["title"],
            "target_esi": case["target_esi"],
            "engine_esi": triage_result.esi_level,
            "matched": attempt["matched"],
        })
    return {
        "results": results,
        "total": len(results),
        "matched": matched_count,
    }


@app.get("/training/cases/{case_id}")
async def get_case(case_id: int):
    """Get a single training case with full transcript."""
    case = get_training_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Training case {case_id} not found")
    return case


@app.post("/training/cases/{case_id}/attempt")
async def attempt_case(case_id: int):
    """Run the triage engine on a training case and record the attempt."""
    case = get_training_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Training case {case_id} not found")

    triage_result = triage(case["transcript"])

    attempt = create_training_attempt(
        case_id=case_id,
        engine_esi=triage_result.esi_level,
        expected_esi=case["target_esi"],
    )

    return {
        "attempt": attempt,
        "triage": triage_result.to_dict(),
        "expected_esi": case["target_esi"],
        "matched": attempt["matched"],
    }


@app.get("/training/stats")
async def training_statistics():
    """Return aggregate training case statistics."""
    return get_training_stats()


# ===========================================================================
#  ADMIN / ANALYTICS
# ===========================================================================


@app.get("/admin/audit")
async def audit_log(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return audit log entries, newest first."""
    return list_audit_entries(limit=limit, offset=offset)


@app.get("/admin/stats/esi-distribution")
async def esi_distribution(since: str | None = Query(None)):
    """Return count of visits grouped by ESI level."""
    return get_esi_distribution(since=since)


@app.get("/admin/stats/common-complaints")
async def common_complaints(limit: int = Query(10, ge=1, le=50)):
    """Return top chief complaints by frequency."""
    return get_common_complaints(limit=limit)
