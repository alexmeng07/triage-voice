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


def _compute_wait_minutes(arrival_time: str | None) -> int | None:
    """Compute minutes elapsed since arrival_time. Returns None if invalid."""
    if not arrival_time:
        return None
    try:
        # Handle ISO strings with or without 'Z' suffix
        ts = arrival_time.replace("Z", "+00:00")
        arrived = datetime.fromisoformat(ts)
        if arrived.tzinfo is None:
            arrived = arrived.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - arrived
        return max(0, int(delta.total_seconds() / 60))
    except (ValueError, TypeError):
        return None


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
    pain_score: int | None = None,
    onset: str | None = None,
    symptom_location: str | None = None,
    status: str = "triaged",
    arrival_time: str | None = None,
    triage_time: str | None = None,
) -> dict[str, Any]:
    """Insert a new visit row and return it as a dict.

    For triage visits: status='triaged', arrival_time and triage_time set to now.
    """
    now = _now_iso()
    arr = arrival_time if arrival_time else now
    tri = triage_time if triage_time else (now if esi_level is not None else None)

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO visits (patient_id, chief_complaint, triage_note,
                                esi_level, triage_method, triage_summary,
                                recommended_action, pain_score, onset,
                                symptom_location, status, arrival_time, triage_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (patient_id, chief_complaint, triage_note,
             esi_level, triage_method, triage_summary,
             recommended_action, pain_score, onset,
             symptom_location, status, arr, tri, now),
        )
        conn.commit()
        visit_id = cursor.lastrowid

        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_visit_by_id(visit_id: int) -> dict[str, Any] | None:
    """Fetch a single visit by primary key, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def update_visit_review(
    visit_id: int,
    reviewed_by: str | None = None,
    reviewed_role: str | None = None,
    final_esi_level: int | None = None,
    disposition: str | None = None,
) -> dict[str, Any] | None:
    """Update review fields on a visit. Returns the updated row or None."""
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE visits
            SET reviewed_by = ?, reviewed_role = ?,
                final_esi_level = ?, disposition = ?
            WHERE id = ?
            """,
            (reviewed_by, reviewed_role, final_esi_level, disposition, visit_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        return _row_to_dict(row) if row else None
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


# ---------------------------------------------------------------------------
# Queue (visit-centric)
# ---------------------------------------------------------------------------

def list_active_queue_visits() -> list[dict[str, Any]]:
    """Return visits with status != 'complete', sorted by acuity then arrival.

    Order: lower ESI first (higher acuity), then older arrival_time.
    Visits with null ESI are placed after those with known acuity.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT v.id AS visit_id, v.patient_id, v.chief_complaint, v.esi_level,
                   v.status, v.arrival_time, v.triage_time, v.created_at,
                   p.first_name, p.last_name, p.date_of_birth
            FROM visits v
            JOIN patients p ON p.id = v.patient_id
            WHERE v.status != 'complete'
            ORDER BY
                CASE WHEN v.esi_level IS NULL THEN 6 ELSE v.esi_level END ASC,
                v.arrival_time ASC
            """
        ).fetchall()
        result = []
        for r in rows:
            d = _row_to_dict(r)
            d["patient_name"] = f"{d['first_name']} {d['last_name']}"
            d["wait_minutes"] = _compute_wait_minutes(d.get("arrival_time"))
            result.append(d)
        return result
    finally:
        conn.close()


def update_visit_status(visit_id: int, status: str) -> dict[str, Any] | None:
    """Update a visit's status. Returns the updated row or None if not found."""
    valid_statuses = {"waiting", "in_triage", "triaged", "with_doctor", "complete"}
    if status not in valid_statuses:
        return None
    conn = get_connection()
    try:
        conn.execute("UPDATE visits SET status = ? WHERE id = ?", (status, visit_id))
        conn.commit()
        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_queue_summary() -> dict[str, int]:
    """Return aggregate counts: waiting, in_triage, triaged, with_doctor."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM visits
            WHERE status != 'complete'
            GROUP BY status
            """
        ).fetchall()
        summary = {"waiting": 0, "in_triage": 0, "triaged": 0, "with_doctor": 0}
        for r in rows:
            s = r["status"]
            if s in summary:
                summary[s] = r["count"]
        return summary
    finally:
        conn.close()


def list_todays_patients_with_visits() -> list[dict[str, Any]]:
    """Return patients who have visits created today, with their latest visit info."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.*,
                   v.id AS latest_visit_id,
                   v.esi_level AS latest_esi_level,
                   v.triage_method AS latest_triage_method,
                   v.chief_complaint AS latest_chief_complaint,
                   v.created_at AS latest_visit_at,
                   v.final_esi_level AS latest_final_esi,
                   v.disposition AS latest_disposition
            FROM patients p
            LEFT JOIN (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY created_at DESC) AS rn
                FROM visits
                WHERE created_at LIKE ? || '%'
            ) v ON p.id = v.patient_id AND v.rn = 1
            WHERE p.id IN (
                SELECT DISTINCT patient_id FROM visits WHERE created_at LIKE ? || '%'
            )
            ORDER BY v.created_at DESC
            """,
            (today, today),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

def create_audit_entry(
    action_type: str,
    patient_id: int | None = None,
    visit_id: int | None = None,
    metadata: str | None = None,
) -> None:
    """Insert an audit log entry."""
    now = _now_iso()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO audit_log (action_type, patient_id, visit_id, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (action_type, patient_id, visit_id, metadata, now),
        )
        conn.commit()
    finally:
        conn.close()


def list_audit_entries(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """Return audit log entries, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Analytics helpers
# ---------------------------------------------------------------------------

def get_esi_distribution(since: str | None = None) -> list[dict[str, Any]]:
    """Return count of visits per ESI level, optionally filtered by date."""
    conn = get_connection()
    try:
        if since:
            rows = conn.execute(
                "SELECT esi_level, COUNT(*) as count FROM visits WHERE created_at >= ? GROUP BY esi_level ORDER BY esi_level",
                (since,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT esi_level, COUNT(*) as count FROM visits GROUP BY esi_level ORDER BY esi_level",
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_common_complaints(limit: int = 10) -> list[dict[str, Any]]:
    """Return top chief complaints by frequency."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT chief_complaint, COUNT(*) as count
            FROM visits
            WHERE chief_complaint IS NOT NULL AND chief_complaint != ''
            GROUP BY chief_complaint
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Training Cases CRUD
# ---------------------------------------------------------------------------

def create_training_case(
    title: str,
    description: str,
    transcript: str,
    target_esi: int,
    rationale: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Insert a training case and return it."""
    now = _now_iso()
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO training_cases (title, description, transcript, target_esi, rationale, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, transcript, target_esi, rationale, category, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM training_cases WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_training_cases() -> list[dict[str, Any]]:
    """Return all training cases."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM training_cases ORDER BY id").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def list_training_cases_with_attempts() -> list[dict[str, Any]]:
    """Return all training cases with their latest attempt (engine_esi, matched).

    Each case dict includes last_engine_esi and last_matched (both None if
    no attempts yet).
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT tc.*,
                   (SELECT ta.engine_esi FROM training_attempts ta
                    WHERE ta.case_id = tc.id
                    ORDER BY ta.created_at DESC LIMIT 1) AS last_engine_esi,
                   (SELECT ta.matched FROM training_attempts ta
                    WHERE ta.case_id = tc.id
                    ORDER BY ta.created_at DESC LIMIT 1) AS last_matched
            FROM training_cases tc
            ORDER BY tc.id
            """
        ).fetchall()
        result = []
        for r in rows:
            d = _row_to_dict(r)
            # SQLite returns None for missing subquery results
            if d.get("last_engine_esi") is None:
                d["last_engine_esi"] = None
            if d.get("last_matched") is None:
                d["last_matched"] = None
            result.append(d)
        return result
    finally:
        conn.close()


def get_training_case_by_id(case_id: int) -> dict[str, Any] | None:
    """Fetch a single training case."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM training_cases WHERE id = ?", (case_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def create_training_attempt(
    case_id: int,
    engine_esi: int,
    expected_esi: int,
    user_identifier: str | None = None,
) -> dict[str, Any]:
    """Record a training attempt."""
    now = _now_iso()
    matched = 1 if engine_esi == expected_esi else 0
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO training_attempts (case_id, engine_esi, expected_esi, matched, user_identifier, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (case_id, engine_esi, expected_esi, matched, user_identifier, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM training_attempts WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_training_stats() -> list[dict[str, Any]]:
    """Return aggregate training statistics per case."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT tc.id as case_id, tc.title, tc.target_esi,
                   COUNT(ta.id) as attempts,
                   SUM(ta.matched) as matches
            FROM training_cases tc
            LEFT JOIN training_attempts ta ON tc.id = ta.case_id
            GROUP BY tc.id
            ORDER BY tc.id
            """,
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()
