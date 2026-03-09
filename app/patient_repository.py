"""Patient & visit CRUD operations against the SQLite database.

Every function here:
- Uses parameterized SQL (? placeholders) — never string interpolation
- Opens and closes its own connection (simple for a prototype)
- Returns plain dicts so the API layer can feed them straight to Pydantic

Tip: look at app/database.py first to see the table schemas.
"""

from __future__ import annotations

import re
import logging
from datetime import datetime, timezone
from typing import Any

from app.database import get_connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _normalize_name(name: str) -> str:
    """Strip whitespace and title-case a name.

    Example: "  john " -> "John"
    """
    return name.strip().title()


def _normalize_phone(phone: str | None) -> str | None:
    """Strip everything except digits from a phone number.

    Example: "(555) 123-4567" -> "5551234567"
    Returns None if the input is None or empty after stripping.
    """
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits if digits else None


def _row_to_dict(row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


# ---------------------------------------------------------------------------
# Patient CRUD
# ---------------------------------------------------------------------------

def create_patient(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    phone: str | None = None,
    sex: str | None = None,
    address: str | None = None,
) -> dict[str, Any]:
    """Insert a new patient and return the full row as a dict.

    Names are title-cased; phone is digit-stripped.
    """
    first_name = _normalize_name(first_name)
    last_name = _normalize_name(last_name)
    phone = _normalize_phone(phone)
    sex = sex.strip().upper() if sex else None       # e.g. "M", "F", "O"
    address = address.strip() if address else None
    now = _now_iso()

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth,
                                  phone, sex, address, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (first_name, last_name, date_of_birth, phone, sex, address, now, now),
        )
        conn.commit()
        patient_id = cursor.lastrowid

        # Fetch the row we just inserted so the caller gets the full record.
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def check_duplicate_patient(
    first_name: str,
    last_name: str,
    date_of_birth: str,
) -> list[dict[str, Any]]:
    """Check if a patient with the same name + DOB already exists.

    Returns a (possibly empty) list of matching rows.
    Used for duplicate warnings during registration.
    """
    first_name = _normalize_name(first_name)
    last_name = _normalize_name(last_name)

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM patients
            WHERE first_name = ? AND last_name = ? AND date_of_birth = ?
            """,
            (first_name, last_name, date_of_birth),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_patient_by_id(patient_id: int) -> dict[str, Any] | None:
    """Fetch a single patient by primary key, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def lookup_patients(
    first_name: str | None = None,
    last_name: str | None = None,
    date_of_birth: str | None = None,
    phone: str | None = None,
) -> list[dict[str, Any]]:
    """Search patients by any combination of identifying fields.

    Only fields that are provided (non-None, non-empty) are used
    in the WHERE clause.  All conditions are AND-ed together.

    Returns a list of matching patient dicts (may be empty).
    """
    # Build WHERE clauses dynamically based on which fields were given.
    conditions: list[str] = []
    params: list[Any] = []

    if first_name and first_name.strip():
        conditions.append("first_name = ?")
        params.append(_normalize_name(first_name))

    if last_name and last_name.strip():
        conditions.append("last_name = ?")
        params.append(_normalize_name(last_name))

    if date_of_birth and date_of_birth.strip():
        conditions.append("date_of_birth = ?")
        params.append(date_of_birth.strip())

    if phone and phone.strip():
        # Phone was stored as digits-only, so normalize the search input too.
        normalized = _normalize_phone(phone)
        if normalized:
            conditions.append("phone = ?")
            params.append(normalized)

    if not conditions:
        # This shouldn't happen — the API endpoint validates first — but
        # return an empty list as a safety measure.
        return []

    sql = "SELECT * FROM patients WHERE " + " AND ".join(conditions)
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def search_patients(query: str) -> list[dict[str, Any]]:
    """Convenience free-text search: matches query against first_name,
    last_name, or phone using SQL LIKE.

    Example: search_patients("doe") matches "Jane Doe" and "John Doe".
    """
    q = f"%{query.strip()}%"
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM patients
            WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
            ORDER BY last_name, first_name
            """,
            (q, q, q),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Visit CRUD
# ---------------------------------------------------------------------------

def create_visit(
    patient_id: int,
    chief_complaint: str | None = None,
    triage_note: str | None = None,
    esi_level: int | None = None,
    triage_method: str | None = None,
    triage_summary: str | None = None,
    recommended_action: str | None = None,
) -> dict[str, Any]:
    """Insert a new visit row and return it as a dict."""
    now = _now_iso()

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO visits (patient_id, chief_complaint, triage_note,
                                esi_level, triage_method, triage_summary,
                                recommended_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (patient_id, chief_complaint, triage_note,
             esi_level, triage_method, triage_summary,
             recommended_action, now),
        )
        conn.commit()
        visit_id = cursor.lastrowid

        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_visits_for_patient(patient_id: int) -> list[dict[str, Any]]:
    """Return all visits for a patient, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM visits WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()
