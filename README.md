# AI Healthcare Assistant

An end-to-end demo platform for helping users describe symptoms, understand insurance constraints, discover nearby doctors, and book an appointment. The project is designed as a DSCI 560 final project scaffold with a Next.js frontend, a FastAPI backend, and mock healthcare data for rapid demos.

## What is included

- Demo registration and login with persistent local credentials
- Symptom intake and rule-based triage
- Insurance parsing and coverage matching
- Ranked doctor recommendations using specialty, distance, availability, insurance, language, and trust signals
- Appointment slot preview and booking confirmation
- AI-style chat and uploaded document explanation endpoints for demos
- Mock data, docs, Docker Compose, and API tests

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

## Demo flow

1. Enter symptoms and get urgency guidance.
2. Upload or type insurance information.
3. Review ranked nearby doctors and the score explanation.
4. Pick a doctor and book an appointment.
5. Use the chat page to ask follow-up questions.

## Notes

- This is a demo-first build backed by mock data rather than live EHR or insurance systems.
- If `OPENAI_API_KEY` is not set, the AI flows automatically fall back to deterministic demo logic.
- If `OPENAI_API_KEY` is set, the backend uses OpenAI Responses API for chat/document explanations and OpenAI Embeddings API for retrieval vectors.
