# AI Healthcare Assistant

AI Healthcare Assistant is a symptom-to-care navigation project built with a Next.js frontend and a FastAPI backend. The current product flow is:

1. collect symptoms and location
2. choose or compare insurance
3. rank doctors with insurance-aware reasoning
4. hand off booking to the provider's official site

This version is optimized for plan-first care navigation, official booking handoff, and LA pilot provider coverage.

## Current product status

- Symptom triage is active
- Insurance parsing and plan advisor are active
- Doctor ranking and final-choice group discussion are active
- Booking is an official third-party handoff, not an in-app confirmation flow
- Official provider/booking coverage is currently focused on the LA pilot

For a concise technical snapshot of the current build, see [docs/current-state.md](/Users/boming/Downloads/DSCI-560-final_project/docs/current-state.md).

## Backend setup

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
cd /Users/boming/Downloads/DSCI-560-final_project
cp .env.example .env
```

Important variables:

- `OPENAI_API_KEY`  
  Optional. Enables OpenAI-backed insurance advisor, decision support, OCR, and retrieval features.
- `POSTGRES_URL`  
  Optional. When available, the API prefers Postgres for persistent reference data.
- carrier-specific provider directory variables such as `BLUE_SHIELD_PROVIDER_DIRECTORY_API_URL`  
  Optional. Enable live carrier provider-directory verification when configured.

## Run the backend

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Optional Postgres

If you want persistent reference data instead of JSON fallback:

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/infra
docker-compose up -d postgres
```

Then restart the API.

## Optional frontend

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/web
npm install
npm run dev
```

## Verify the running backend

- Health check: `http://127.0.0.1:8000/api/v1/health`
- API docs: `http://127.0.0.1:8000/docs`

What to look for in `/health`:

- `reference_data_backend: "postgres"` means the API is using Postgres
- `reference_data_backend: "json_fallback"` means the API is still using local JSON reference data

## Important notes

- The site does not complete appointments internally. It recommends doctors and hands booking off to the provider's official website.
- Official booking handoff is currently strongest in the LA pilot flow.
- Quick access login still exists for local testing.
- The current UI is official-first: if live verification or an official booking link is missing, the interface now says so directly instead of fabricating a stronger result.
