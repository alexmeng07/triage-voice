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
    create_patient,
    create_visit,
    get_patient_by_id,
    list_visits_for_patient,
    lookup_patients,
    search_patients,
)
from app.patient_schemas import (
    CreatePatientRequest,
    CreateVisitRequest,
    PatientLookupRequest,
    PatientLookupResponse,
    PatientResponse,
    RegisterPatientResponse,
    TriageVisitResponse,
    VisitResponse,
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
    "audio/flac",
}

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
    if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
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


@app.get("/patients/search", response_model=PatientLookupResponse)
async def patient_search(
    q: str = Query(..., min_length=1, description="Free-text search for patients"),
) -> PatientLookupResponse:
    """Convenience search: matches query against first_name, last_name, or phone."""
    matches = search_patients(q)
    return PatientLookupResponse(
        matches=[PatientResponse(**m) for m in matches],
        count=len(matches),
    )


@app.post("/patients/register", response_model=RegisterPatientResponse)
async def register_patient(req: CreatePatientRequest) -> RegisterPatientResponse:
    """Create a new patient record.

    Returns the created patient.  If a patient with the same name + DOB
    already exists, a duplicate_warning is included (but the patient is
    still created — this is just an informational heads-up).
    """
    # Check for possible duplicates before inserting.
    dupes = check_duplicate_patient(req.first_name, req.last_name, req.date_of_birth)
    warning: str | None = None
    if dupes:
        ids = ", ".join(str(d["id"]) for d in dupes)
        warning = (
            f"Possible duplicate(s) found with same name and DOB "
            f"(existing patient IDs: {ids}). Patient was still created."
        )

    patient = create_patient(
        first_name=req.first_name,
        last_name=req.last_name,
        date_of_birth=req.date_of_birth,
        phone=req.phone,
        sex=req.sex,
        address=req.address,
    )

    return RegisterPatientResponse(
        patient=PatientResponse(**patient),
        duplicate_warning=warning,
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

    # Step 2: run triage (reuses existing engine — no duplication!)
    triage_result = triage(req.transcript_or_note)

    # Step 3: store visit
    visit = create_visit(
        patient_id=patient_id,
        chief_complaint=req.transcript_or_note,  # store the raw input as chief complaint
        triage_note=req.transcript_or_note,
        esi_level=triage_result.esi_level,
        triage_method=triage_result.method,
        triage_summary=triage_result.summary,
        recommended_action=triage_result.recommended_action,
    )

    # Step 4: return combined response
    return TriageVisitResponse(
        visit=VisitResponse(**visit),
        triage=triage_result.to_dict(),
    )
