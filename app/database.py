"""SQLite database setup for patient registration.

This module handles:
- Creating the database file and tables on first run
- Providing a connection helper for other modules

The DB file lives at data/triage_voice.db (auto-created).
Uses Python stdlib sqlite3 — no ORM needed for this prototype.
"""

from __future__ import annotations

import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Where the SQLite file lives, relative to the project root.
# The "data/" directory already exists in the repo.
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "triage_voice.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set to sqlite3.Row.

    sqlite3.Row lets you access columns by name (like a dict) instead of
    by index, which makes the code much more readable.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # enables  row["column_name"]
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK constraints
    return conn


# ---------------------------------------------------------------------------
# Table creation SQL
# ---------------------------------------------------------------------------

_CREATE_PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name  TEXT    NOT NULL,
    last_name   TEXT    NOT NULL,
    date_of_birth TEXT  NOT NULL,   -- stored as ISO string YYYY-MM-DD
    phone       TEXT,
    sex         TEXT,
    address     TEXT,
    created_at  TEXT    NOT NULL,   -- ISO-8601 UTC timestamp
    updated_at  TEXT    NOT NULL    -- ISO-8601 UTC timestamp
);
"""

_CREATE_VISITS_TABLE = """
CREATE TABLE IF NOT EXISTS visits (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL,
    chief_complaint     TEXT,
    triage_note         TEXT,
    esi_level           INTEGER,
    triage_method       TEXT,
    triage_summary      TEXT,
    recommended_action  TEXT,
    created_at          TEXT    NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
"""

# Indexes speed up the most common lookup patterns.
_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_patients_last_name ON patients(last_name);",
    "CREATE INDEX IF NOT EXISTS idx_patients_phone     ON patients(phone);",
    "CREATE INDEX IF NOT EXISTS idx_patients_dob       ON patients(date_of_birth);",
    "CREATE INDEX IF NOT EXISTS idx_patients_last_dob  ON patients(last_name, date_of_birth);",
]


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the database file and tables if they don't already exist.

    Safe to call multiple times — every statement uses IF NOT EXISTS.
    Called automatically when the FastAPI app starts up.
    """
    # Make sure the parent directory exists (it should, but just in case).
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        conn.execute(_CREATE_PATIENTS_TABLE)
        conn.execute(_CREATE_VISITS_TABLE)
        for idx_sql in _CREATE_INDEXES:
            conn.execute(idx_sql)
        conn.commit()
        logger.info("Database initialized at %s", DB_PATH)
    finally:
        conn.close()
