"""Pydantic models for patient registration / lookup / visit endpoints.

These are separate from the existing api_schemas.py to keep the patient
feature isolated.  The existing triage schemas are imported where needed
(e.g. TriageVisitResponse reuses TriageResponse).
"""

from __future__ import annotations

import re
from pydantic import BaseModel, Field, field_validator

from app.api_schemas import TriageResponse


# ---------------------------------------------------------------------------
# Patient — Requests
# ---------------------------------------------------------------------------

class CreatePatientRequest(BaseModel):
    """Body for POST /patients/register."""
    first_name: str = Field(..., min_length=1, max_length=100, description="Patient first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Patient last name")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    phone: str | None = Field(None, max_length=30, description="Phone number (optional)")
    sex: str | None = Field(None, max_length=10, description="Sex: M, F, or O (optional)")
    address: str | None = Field(None, max_length=300, description="Mailing address (optional)")

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob_format(cls, v: str) -> str:
        """Make sure the date looks like YYYY-MM-DD (basic check)."""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v.strip()):
            raise ValueError("date_of_birth must be in YYYY-MM-DD format")
        return v.strip()


class PatientLookupRequest(BaseModel):
    """Body for POST /patients/lookup.

    At least one field must be provided — the API endpoint checks this.
    """
    first_name: str | None = Field(None, description="First name (exact match)")
    last_name: str | None = Field(None, description="Last name (exact match)")
    date_of_birth: str | None = Field(None, description="DOB in YYYY-MM-DD")
    phone: str | None = Field(None, description="Phone number")


# ---------------------------------------------------------------------------
# Patient — Responses
# ---------------------------------------------------------------------------

class PatientResponse(BaseModel):
    """Full patient record returned from the API."""
    id: int
    first_name: str
    last_name: str
    date_of_birth: str
    phone: str | None = None
    sex: str | None = None
    address: str | None = None
    created_at: str
    updated_at: str


# PatientMatch is the same shape as PatientResponse — just an alias for
# clarity in lookup results.
PatientMatch = PatientResponse


class PatientLookupResponse(BaseModel):
    """Wrapper returned from POST /patients/lookup."""
    matches: list[PatientMatch]
    count: int


class RegisterPatientResponse(BaseModel):
    """Returned from POST /patients/register.

    Includes the created patient plus an optional duplicate warning.
    """
    patient: PatientResponse
    duplicate_warning: str | None = None
    duplicates: list[PatientResponse] = []


# ---------------------------------------------------------------------------
# Visit — Request / Response
# ---------------------------------------------------------------------------

class CreateVisitRequest(BaseModel):
    """Body for POST /patients/{patient_id}/triage-visit."""
    transcript_or_note: str = Field(
        ..., min_length=1, max_length=10000,
        description="The patient transcript or free-text note to triage",
    )
    pain_score: int | None = Field(None, ge=0, le=10, description="Pain score 0-10")
    onset: str | None = Field(None, max_length=100, description="Symptom onset timeframe")
    symptom_location: str | None = Field(None, max_length=200, description="Location of symptoms")


class VisitReviewRequest(BaseModel):
    """Body for PATCH /visits/{visit_id}/review — clinician sign-off fields."""
    reviewed_by: str | None = Field(None, max_length=100, description="Name of reviewing clinician")
    reviewed_role: str | None = Field(None, max_length=100, description="Role of reviewing clinician")
    final_esi_level: int | None = Field(None, ge=1, le=5, description="Clinician-determined ESI level")
    disposition: str | None = Field(None, max_length=300, description="Patient disposition")


class VisitResponse(BaseModel):
    """A single visit record."""
    id: int
    patient_id: int
    chief_complaint: str | None = None
    triage_note: str | None = None
    esi_level: int | None = None
    triage_method: str | None = None
    triage_summary: str | None = None
    recommended_action: str | None = None
    pain_score: int | None = None
    onset: str | None = None
    symptom_location: str | None = None
    reviewed_by: str | None = None
    reviewed_role: str | None = None
    final_esi_level: int | None = None
    disposition: str | None = None
    status: str | None = None
    arrival_time: str | None = None
    triage_time: str | None = None
    created_at: str


class TriageVisitResponse(BaseModel):
    """Combined response from POST /patients/{id}/triage-visit.

    Contains the stored visit record AND the full triage result.
    """
    visit: VisitResponse
    triage: TriageResponse


# ---------------------------------------------------------------------------
# Queue (visit-centric)
# ---------------------------------------------------------------------------

class QueueVisitResponse(BaseModel):
    """A visit in the active queue (GET /queue)."""
    visit_id: int
    patient_id: int
    patient_name: str
    date_of_birth: str
    chief_complaint: str | None = None
    esi_level: int | None = None
    status: str
    arrival_time: str | None = None
    triage_time: str | None = None
    wait_minutes: int | None = None


VALID_QUEUE_STATUSES = {"waiting", "in_triage", "triaged", "with_doctor", "complete"}


class VisitStatusUpdateRequest(BaseModel):
    """Body for PATCH /visits/{visit_id}/status."""
    status: str = Field(..., description="One of: waiting, in_triage, triaged, with_doctor, complete")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_QUEUE_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(VALID_QUEUE_STATUSES))}"
            )
        return v
