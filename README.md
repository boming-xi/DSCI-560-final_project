# AI Healthcare Assistant

An end-to-end demo platform for helping users describe symptoms, understand insurance constraints, discover nearby doctors, and book an appointment. The project is designed as a DSCI 560 final project scaffold with a Next.js frontend, a FastAPI backend, and mock healthcare data for rapid demos.

Postgres is an open-source relational database. In this project it now acts as the persistent reference-data store for doctors, clinics, and insurance plans, while the old JSON files remain as a safe fallback.

## What is included

- Demo registration and login with persistent local credentials
- Symptom intake and rule-based triage
- Insurance parsing and coverage matching
- Ranked doctor recommendations using specialty, distance, availability, insurance, language, and trust signals
- Appointment slot preview and booking confirmation
- AI-style chat and uploaded document explanation endpoints for demos
- Mock data, docs, Docker Compose, and API tests
- Postgres-backed reference data bootstrap for doctors, clinics, and insurance plans
- External provider directory sync scaffold for clinics and doctors
- External scheduling sync scaffold for appointment slots

## Repository layout

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `packages/mock-data`: doctors, clinics, and insurance fixtures
- `docs`: architecture, API contract, prompts, and demo scenarios
- `infra`: local Postgres and Qdrant support

## Quick start

### 1. Backend

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If you want real OpenAI-powered chat, document explanation, and embeddings:

```bash
cd /Users/boming/Downloads/DSCI-560-final_project
cp .env.example .env
```

Then set `OPENAI_API_KEY` in `.env`. Optional model settings:

- `OPENAI_CHAT_MODEL=gpt-5.4-mini`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `OPENAI_REASONING_EFFORT=low`
- `OPENAI_MAX_OUTPUT_TOKENS=700`

If you want persistent provider and insurance reference data in Postgres:

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/infra
docker-compose up -d postgres
```

The API now bootstraps doctors, clinics, and insurance plans into Postgres on startup when `POSTGRES_URL` is reachable. You can also seed manually:

```bash
cd /Users/boming/Downloads/DSCI-560-final_project
make api-seed
```

If Postgres was not running when the API first started, restart the API after the database comes up so the bootstrap step can run against Postgres instead of JSON fallback.

### External provider sync

The backend also includes a provider-directory sync scaffold that can import clinics and doctors into Postgres from either:

- A local JSON snapshot
- A remote JSON API

Snapshot mode is the default. A demo snapshot is included at `packages/mock-data/provider_directory_snapshot.json`.
You can also use:

- `PROVIDER_DIRECTORY_SOURCE=nppes` for the official CMS NPPES/NPI Registry API
- `PROVIDER_DIRECTORY_SOURCE=http` for a custom JSON directory feed

Environment options:

- `PROVIDER_DIRECTORY_SOURCE=snapshot` or `http`
- `PROVIDER_DIRECTORY_SOURCE=nppes`
- `PROVIDER_DIRECTORY_SNAPSHOT_FILE=/absolute/path/to/provider_snapshot.json`
- `PROVIDER_DIRECTORY_API_URL=https://example.com/provider-directory`
- `PROVIDER_DIRECTORY_API_KEY=...`
- `PROVIDER_DIRECTORY_API_KEY_HEADER=Authorization`
- `PROVIDER_DIRECTORY_QUERY_CITY=Los Angeles`
- `PROVIDER_DIRECTORY_QUERY_STATE=CA`
- `PROVIDER_DIRECTORY_QUERY_TAXONOMY=Family Medicine`

Recommended official NPPES setup:

```bash
PROVIDER_DIRECTORY_SOURCE=nppes
PROVIDER_DIRECTORY_API_URL=https://npiregistry.cms.hhs.gov/api/
PROVIDER_DIRECTORY_QUERY_CITY=Los Angeles
PROVIDER_DIRECTORY_QUERY_STATE=CA
PROVIDER_DIRECTORY_QUERY_TAXONOMY=Family Medicine
```

Run a sync from the command line:

```bash
cd /Users/boming/Downloads/DSCI-560-final_project
make api-sync-providers
```

Or trigger it through the authenticated API:

```bash
POST /api/v1/providers/sync
```

The expected JSON payload shape is:

```json
{
  "source": "external_provider_directory",
  "clinics": [
    {
      "external_id": "clinic-123",
      "name": "Example Clinic",
      "care_types": ["primary_care"],
      "address": "123 Main St",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90007",
      "latitude": 34.02,
      "longitude": -118.28,
      "languages": ["English"],
      "open_weekends": false,
      "urgent_care": false,
      "phone": "(000) 000-0000"
    }
  ],
  "doctors": [
    {
      "external_id": "doctor-123",
      "name": "Dr. Example",
      "specialty": "Family Medicine",
      "care_types": ["primary_care"],
      "clinic_external_id": "clinic-123",
      "years_experience": 10,
      "languages": ["English"],
      "rating": 4.7,
      "review_count": 50,
      "accepted_insurance": ["usc-aetna-student"],
      "availability_days": 2,
      "telehealth": true,
      "gender": "Female",
      "profile_blurb": "Imported from provider directory"
    }
  ]
}
```

### External scheduling sync

The backend also includes a scheduling sync scaffold for importing appointment slots into Postgres and using them in `/api/v1/booking/slots/{doctor_id}` before falling back to demo-generated availability.

Supported sources:

- A local JSON snapshot
- A remote JSON API
- A FHIR `Slot` endpoint

Scheduling environment options:

- `SCHEDULING_SOURCE=snapshot`, `http`, or `fhir`
- `SCHEDULING_SNAPSHOT_FILE=/absolute/path/to/availability_snapshot.json`
- `SCHEDULING_API_URL=https://example.com/scheduling-feed`
- `SCHEDULING_API_KEY=...`
- `SCHEDULING_API_KEY_HEADER=Authorization`
- `SCHEDULING_SLOT_STALE_HOURS=24`

Recommended FHIR setup:

```bash
SCHEDULING_SOURCE=fhir
SCHEDULING_API_URL=https://hapi.fhir.org/baseR4/Slot
SCHEDULING_FHIR_COUNT=50
```

For Epic sandbox style FHIR servers, point `SCHEDULING_API_URL` at the server's `Slot` search endpoint and provide the OAuth bearer token in `SCHEDULING_API_KEY`.

Run a slot sync from the command line:

```bash
cd /Users/boming/Downloads/DSCI-560-final_project
make api-sync-availability
```

Or trigger it through the authenticated API:

```bash
POST /api/v1/booking/sync-slots
```

The expected scheduling payload shape is:

```json
{
  "source": "external_scheduling",
  "slots": [
    {
      "external_id": "slot-123",
      "doctor_id": "dr-michelle-lin",
      "clinic_id": "clinic-union",
      "start": "2026-04-15T16:00:00-07:00",
      "end": "2026-04-15T16:30:00-07:00",
      "label": "Wed Apr 15, 04:00 PM",
      "available": true,
      "appointment_mode": "In person",
      "comments": "Imported from external schedule feed"
    }
  ]
}
```

### 2. Frontend

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/web
npm install
npm run dev
```

### 3. Open the demo

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

### Demo authentication

- Register at `/register`
- Log in at `/login`
- Demo users are stored locally in `apps/api/data/demo_users.json`
- Passwords are hashed before being stored
- Reference data health is exposed at `/api/v1/health` via `reference_data_backend`

## Demo flow

1. Enter symptoms and get urgency guidance.
2. Choose an insurance path:
   existing insurance upload, or AI insurance advisor for plan selection.
3. Review ranked nearby doctors and the score explanation.
4. Pick a doctor and book an appointment.
5. Use the chat page to ask follow-up questions.

## Insurance advisor and plan-first flow

The insurance page now has a two-step branch:

- `Step 1`: choose whether you already have insurance
- `Step 2`: either upload your current plan details or use the AI advisor to compare plans first

If the advisor recommends a plan and you click `Use this plan for doctor search`, the selected plan, purchase link, and network directory URL are carried into the doctor flow automatically.

## Real-time carrier provider directory verification

Doctor ranking now tries a live carrier provider directory check first when a carrier-specific API is configured. If the live check does not confirm a match, the app safely falls back to stored carrier and network aliases already attached to the doctor record.

Supported carrier env patterns:

- `AETNA_PROVIDER_DIRECTORY_API_TYPE=fhir|json`
- `AETNA_PROVIDER_DIRECTORY_API_URL=...`
- `AETNA_PROVIDER_DIRECTORY_API_KEY=...`
- `AETNA_PROVIDER_DIRECTORY_API_KEY_QUERY_PARAM=...`
- `ANTHEM_PROVIDER_DIRECTORY_API_TYPE=fhir|json`
- `BLUE_SHIELD_PROVIDER_DIRECTORY_API_TYPE=fhir|json`
- `CIGNA_PROVIDER_DIRECTORY_API_TYPE=fhir|json`
- `HEALTH_NET_PROVIDER_DIRECTORY_API_TYPE=fhir|json`
- `KAISER_PROVIDER_DIRECTORY_API_TYPE=fhir|json`
- `UNITEDHEALTHCARE_PROVIDER_DIRECTORY_API_TYPE=fhir|json`

If a carrier sandbox expects credentials in the query string instead of a header, set `*_PROVIDER_DIRECTORY_API_KEY_QUERY_PARAM`. For example, Blue Shield of California's sandbox documentation shows `clientId` as a query parameter for provider directory calls.

The app currently recognizes these carriers from the selected plan metadata and will call the corresponding live provider directory client when configured:

- Aetna
- Anthem Blue Cross
- Blue Shield of California
- Cigna
- Health Net
- Kaiser Permanente
- UnitedHealthcare

## Notes

- This is a demo-first build backed by mock data rather than live EHR or insurance systems.
- The API prefers Postgres for doctor, clinic, and insurance reference data, and falls back to JSON fixtures if the database is unavailable.
- External provider sync currently targets clinics and doctors first; insurance directory sync can follow the same pattern.
- If `OPENAI_API_KEY` is not set, the AI flows automatically fall back to deterministic demo logic.
- If `OPENAI_API_KEY` is set, the backend uses OpenAI Responses API for chat/document explanations and OpenAI Embeddings API for retrieval vectors.
