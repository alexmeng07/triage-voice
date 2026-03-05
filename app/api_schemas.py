"""Pydantic models for API request/response validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class TriageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Patient transcript or chief complaint text")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class TriageResponse(BaseModel):
    esi_level: int
    red_flags: list[str]
    summary: str
    recommended_action: str
    confidence: float | None = None
    method: str
    disclaimer: str


class AudioTriageResponse(TriageResponse):
    transcript: str


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    ml_ready: bool
    mode: str
    message: str | None = None


class VersionResponse(BaseModel):
    app: str = "triage-voice"
    version: str = "0.1.0"
    git_commit: str | None = None
