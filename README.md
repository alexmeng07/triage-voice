# triage-voice

ESI triage simulation API with patient registration, lookup, and visit tracking.

> **Disclaimer** — This is a simulation / prototype and not real medical software.

## Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. (Optional) Seed test data — 4 patients, 2 visits
python -m scripts.seed_patients

# 3. Start the API server (http://127.0.0.1:8000)
python api_server.py
```

The SQLite database is created automatically at `data/triage_voice.db` on first startup.

## Frontend (Receptionist Intake)

The `frontend/` directory contains a Next.js app for the clinic front-desk workflow: patient search, registration, detail view, and triage visit creation.

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

The frontend calls the FastAPI backend at `http://localhost:8000` by default.
Override with the `NEXT_PUBLIC_API_URL` environment variable (see `frontend/.env.example`).

---

## API Reference

### System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check → `{ "status": "ok" }` |
| GET | `/ready` | ML model readiness |
| GET | `/version` | App version + git commit |

### Triage

| Method | Path | Description |
|--------|------|-------------|
| POST | `/triage` | Triage from text input |
| POST | `/triage/audio` | Triage from audio file upload |

### Patients

| Method | Path | Description |
|--------|------|-------------|
| GET | `/patients/search?q={query}` | Free-text patient search |
| POST | `/patients/register` | Register a new patient |
| POST | `/patients/lookup` | Structured patient lookup |
| GET | `/patients/{patient_id}` | Get patient by ID |
| GET | `/patients/{patient_id}/visits` | List visits for a patient |
| POST | `/patients/{patient_id}/triage-visit` | Run triage and create a visit |

---

### POST /patients/register

Register a new patient record.

**Request:**

```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "date_of_birth": "1990-05-15",
  "phone": "555-123-4567",
  "sex": "F",
  "address": "123 Main St"
}
```

**Response:**

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

If a patient with the same name and DOB already exists, `duplicate_warning` contains an informational message. The patient is still created.

---

### POST /patients/lookup

Search by any combination of `first_name`, `last_name`, `date_of_birth`, `phone`. At least one field required. All provided fields are AND-ed.

**Request:**

```json
{
  "last_name": "Doe",
  "date_of_birth": "1990-05-15"
}
```

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
      "created_at": "2025-01-15T12:00:00+00:00",
      "updated_at": "2025-01-15T12:00:00+00:00"
    }
  ],
  "count": 1
}
```

---

### GET /patients/search?q={query}

Free-text search against first name, last name, and phone. Returns the same `{ matches, count }` wrapper as `/patients/lookup`.

**Example:** `GET /patients/search?q=Doe`

---

### GET /patients/{patient_id}

Returns a single patient object. `404` if not found.

---

### GET /patients/{patient_id}/visits

Returns a list of `VisitResponse` objects, newest first. `404` if the patient doesn't exist.

---

### POST /patients/{patient_id}/triage-visit

Run the triage engine on a transcript/note and create a visit record.

**Request:**

```json
{
  "transcript_or_note": "I have a severe headache and mild fever since yesterday"
}
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
    "created_at": "2025-01-15T12:00:00+00:00"
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

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed origins |
| `ELEVENLABS_API_KEY` | — | Required only for `/triage/audio` (speech-to-text) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend: backend API base URL |

---

## Seed Data

```bash
python -m scripts.seed_patients
```

Inserts 4 patients (Jane Doe, John Smith, Maria Garcia, Robert Chen) and 2 sample visits. Safe to run multiple times.

---

## Project Structure

```
app/
  api.py                 # FastAPI app + all routes
  api_schemas.py         # Triage request/response models
  patient_schemas.py     # Patient request/response models
  patient_repository.py  # Patient & visit CRUD (SQLite)
  database.py            # SQLite setup + connection
  schemas.py             # TriageResult dataclass
  triage_engine.py       # Hybrid triage (rules + ML)
  triage_rules.py        # Rule-based ESI 1/2
  ml_model.py            # ESI 3/4/5 classifier
  stt.py                 # Speech-to-text (ElevenLabs)
  cli.py                 # CLI commands
scripts/
  seed_patients.py       # Seed test data
  validate_esi.py        # Validate JSONL training data
training/
  train_esi345.py        # Train ESI 3/4/5 model
frontend/                # Next.js receptionist frontend
  src/lib/api.ts         #   Typed API client
  src/lib/types.ts       #   TypeScript interfaces (mirror backend)
  src/components/        #   Reusable UI components
  src/app/               #   Pages (App Router)
data/
  triage_voice.db        # SQLite database (auto-created, gitignored)
  esi345_sample.jsonl    # Sample training data
```
