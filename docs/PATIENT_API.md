# Patient Registration & Lookup API

This document covers the patient registration, lookup, and triage-visit endpoints added to the triage-voice API.

> **Disclaimer**: This is a simulation / prototype — not real medical software.

---

## New Files

| File | Purpose |
|------|---------|
| `app/database.py` | SQLite setup — creates tables and indexes on startup |
| `app/patient_repository.py` | CRUD functions for patients and visits (parameterized SQL) |
| `app/patient_schemas.py` | Pydantic request/response models for patient endpoints |
| `scripts/seed_patients.py` | Inserts 3 example patients for local testing |

## Modified Files

| File | What changed |
|------|-------------|
| `app/api.py` | Added 6 new endpoints + lifespan DB init (existing routes untouched) |
| `app/cli.py` | Added `--register-patient` and `--lookup-patient` CLI commands |
| `.gitignore` | Added `data/*.db` |

---

## Where the SQLite File Lives

```
data/triage_voice.db
```

Created automatically when the API server starts (or when you run the seed script / CLI commands). The file is git-ignored.

---

## How to Start the API

```bash
python api_server.py
```

The server runs on `http://127.0.0.1:8000` by default. The patient database initializes automatically on startup.

---

## Seed Test Data (Optional)

```bash
python -m scripts.seed_patients
```

Inserts 3 fake patients: Jane Doe, John Smith, Maria Garcia.

---

## API Endpoints

### Register a Patient

```bash
curl -X POST http://localhost:8000/patients/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "phone": "555-123-4567",
    "sex": "F",
    "address": "123 Main St"
  }'
```

**Response** (201-style, returned as 200):
```json
{
  "patient": {
    "id": 1,
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "phone": "5551234567",
    "sex": "F",
    "address": "123 Main St",
    "created_at": "2025-01-15T12:00:00+00:00",
    "updated_at": "2025-01-15T12:00:00+00:00"
  },
  "duplicate_warning": null
}
```

If a patient with the same name + DOB already exists, `duplicate_warning` will contain a message with the existing patient IDs.

---

### Look Up a Patient

```bash
curl -X POST http://localhost:8000/patients/lookup \
  -H "Content-Type: application/json" \
  -d '{"last_name": "Doe"}'
```

You can search by any combination of: `first_name`, `last_name`, `date_of_birth`, `phone`. At least one field is required.

**Response:**
```json
{
  "matches": [
    {
      "id": 1,
      "first_name": "Jane",
      "last_name": "Doe",
      "date_of_birth": "1990-05-15",
      "phone": "5551234567",
      "sex": "F",
      "address": "123 Main St",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "count": 1
}
```

---

### Search Patients (Convenience)

```bash
curl "http://localhost:8000/patients/search?q=Doe"
```

Free-text search against first_name, last_name, and phone.

---

### Get Patient by ID

```bash
curl http://localhost:8000/patients/1
```

Returns `404` if not found.

---

### Create a Triage Visit

```bash
curl -X POST http://localhost:8000/patients/1/triage-visit \
  -H "Content-Type: application/json" \
  -d '{"transcript_or_note": "I have a severe headache and mild fever since yesterday"}'
```

**Response:**
```json
{
  "visit": {
    "id": 1,
    "patient_id": 1,
    "chief_complaint": "I have a severe headache and mild fever since yesterday",
    "triage_note": "I have a severe headache and mild fever since yesterday",
    "esi_level": 3,
    "triage_method": "rule",
    "triage_summary": "...",
    "recommended_action": "...",
    "created_at": "..."
  },
  "triage": {
    "esi_level": 3,
    "red_flags": [],
    "summary": "...",
    "recommended_action": "...",
    "confidence": null,
    "method": "rule",
    "disclaimer": "This is a simulation and not medical advice. Always consult a healthcare professional."
  }
}
```

---

### List Visits for a Patient

```bash
curl http://localhost:8000/patients/1/visits
```

Returns visits newest-first. Returns `404` if the patient doesn't exist.

---

## CLI Commands

```bash
# Register a patient interactively
python -m app.cli --register-patient

# Look up a patient interactively
python -m app.cli --lookup-patient
```

---

## No New Dependencies

This feature uses only Python stdlib `sqlite3` — no new packages to install.
