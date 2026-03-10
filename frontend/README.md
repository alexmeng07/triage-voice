# triage-voice frontend

Receptionist patient-intake frontend for the triage-voice API.

## Setup

```bash
npm install
cp .env.example .env.local   # optional — defaults work for local dev
npm run dev                   # → http://localhost:3000
```

The backend must be running at `http://localhost:8000` (or set `NEXT_PUBLIC_API_URL`).

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Home — Find Patient / Register Patient |
| `/patients` | Search & lookup |
| `/patients/register` | New patient form |
| `/patients/[id]` | Patient detail + visit history |
| `/patients/[id]/triage` | New triage visit |

## Stack

- Next.js 16 (App Router, TypeScript)
- Tailwind CSS 4
- Lucide React (icons)
- No external state library — local `useState` + fetch
