"""FastAPI application — HTTP layer over the triage pipeline."""

from __future__ import annotations

import logging
import os
import subprocess

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(
    title="triage-voice",
    version=APP_VERSION,
    description="ESI triage simulation API (not medical advice).",
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

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


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
