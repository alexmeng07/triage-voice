"""Structured triage note model and helpers. Pure logic, no IO."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

from app.schemas import TriageResult
from app.triage_engine import triage


@dataclass
class TriageCase:
    """Structured representation of a triage case collected via interview or form."""

    age: Optional[int]
    complaint: str
    onset: str
    severity: Optional[int]  # 0-10 scale, None if unknown
    red_flags: List[str]  # human-readable labels like "trouble breathing", "chest pain"


def case_to_note(case: TriageCase) -> str:
    """Convert a TriageCase into a standardized free-text note."""
    age_part = f"Age: {case.age}." if case.age is not None else "Age: unknown."
    complaint = case.complaint.strip() or "unspecified."
    complaint_part = f"Complaint: {complaint}"

    onset = case.onset.strip() or "unknown"
    onset_part = f"Onset: {onset}."

    if case.severity is not None:
        severity_part = f"Severity: {case.severity}/10."
    else:
        severity_part = "Severity: unknown."

    if case.red_flags:
        # Join and ensure phrases are compatible with existing rules patterns.
        red_flags_text = ", ".join(case.red_flags)
        red_flags_part = f"Red flags: {red_flags_text}."
    else:
        red_flags_part = "Red flags: none mentioned."

    return " ".join(
        [
            age_part,
            complaint_part,
            onset_part,
            severity_part,
            red_flags_part,
        ]
    )


def triage_note(note: str) -> TriageResult:
    """Run triage on a standardized triage note (routes through hybrid engine)."""
    return triage(note or "")


def missing_info_hints(text: str) -> List[str]:
    """
    Heuristically identify key pieces of information that appear to be missing.

    This is intentionally simple and conservative. It never diagnoses; it only
    suggests what extra details could improve triage.
    """
    hints: List[str] = []
    text_norm = (text or "").lower()

    # Age: look for patterns like "54 years old", "54 yo", "age 54", or "Age: 54" (from case_to_note).
    # Also check for "Age: unknown" which means it was explicitly marked as unknown.
    age_pattern = re.compile(
        r"\b\d{1,3}\s*(?:years?\s*old|yo)\b"
        r"|\bage[:\s]+\d{1,3}\b"
    )
    age_unknown_pattern = re.compile(r"\bage[:\s]+unknown\b")
    if not age_pattern.search(text_norm) and not age_unknown_pattern.search(text_norm):
        hints.append("Age not mentioned.")

    # Severity: look for 0-10 style, descriptive words, or "Severity: N/10" (from case_to_note).
    # Also check for "Severity: unknown" which means it was explicitly marked as unknown.
    severity_pattern = re.compile(
        r"\b(?:pain|severity)[:\s]*(?:is\s*)?\d{1,2}\s*(?:out\s+of\s+10|/10)\b"
        r"|\b(mild|moderate|severe)\s+(?:pain|headache|discomfort)\b"
        r"|\bseverity[:\s]+\d{1,2}/10\b"
    )
    severity_unknown_pattern = re.compile(r"\bseverity[:\s]+unknown\b")
    if not severity_pattern.search(text_norm) and not severity_unknown_pattern.search(text_norm):
        hints.append("Pain severity (0–10) not mentioned.")

    # Onset/duration: look for temporal phrases or "Onset: <value>" (from case_to_note).
    # Also check for "Onset: unknown" which means it was explicitly marked as unknown.
    onset_pattern = re.compile(
        r"\bsince\b|\bfor\s+\d+\s+(?:minutes?|hours?|days?|weeks?)\b|\bstarted\b"
        r"|\bonset[:\s]+(?!unknown\b)\S+"
    )
    onset_unknown_pattern = re.compile(r"\bonset[:\s]+unknown\b")
    if not onset_pattern.search(text_norm) and not onset_unknown_pattern.search(text_norm):
        hints.append("Onset/duration not mentioned.")

    return hints

