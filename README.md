# AI Healthcare Assistant

This project provides symptom triage, insurance guidance, doctor ranking, and official booking handoff. The current live flow is optimized for Los Angeles pilot providers with official public profile and booking pages.

For a concise technical snapshot of the current build, see [docs/current-state.md](/Users/boming/Downloads/DSCI-560-final_project/docs/current-state.md). Reference datasets now live under [packages/reference-data](/Users/boming/Downloads/DSCI-560-final_project/packages/reference-data).

## Backend setup

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment setup

```bash
cd /Users/boming/Downloads/DSCI-560-final_project
cp .env.example .env
```

Only these variables matter for the default local backend flow:

- `OPENAI_API_KEY`  
  Optional. Enables OpenAI-backed insurance advisor, OCR, and explanation features.
- `DEMO_AUTH_SECRET`  
  Used for local demo auth tokens.
- `POSTGRES_URL`  
  Optional. Used only if you want persistent reference data instead of JSON fallback.

The other provider-directory and scheduling variables in `.env.example` are advanced optional integrations. They are only needed if you want to enable external provider sync or live carrier verification.

## Run the backend

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Frontend setup

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/web
npm install
```

## Run the frontend

```bash
cd /Users/boming/Downloads/DSCI-560-final_project/apps/web
npm run dev
```

Frontend default URL:

- `http://localhost:3000`

## Verify the backend

- Health check: `http://127.0.0.1:8000/api/v1/health`
- API docs: `http://127.0.0.1:8000/docs`

What to look for in `/health`:

- `reference_data_backend: "postgres"` means persistent reference data is active
- `reference_data_backend: "json_fallback"` means the API is running from local JSON reference data

## Important notes

- This site does not complete appointments internally. It recommends doctors and hands booking off to official provider websites.
- The current public-doctor experience is official-first: only doctors with public official profile and booking paths are shown in the main ranking flow.
- Los Angeles pilot coverage currently includes UCLA Health and Keck Medicine of USC public provider paths.
- `packages/reference-data` is the current reference-data home. It contains official derived plan data, curated official-provider datasets, and a few optional connector snapshots used for local sync/testing.
