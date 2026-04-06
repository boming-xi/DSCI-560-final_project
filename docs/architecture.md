# Architecture

## Overview

The system is organized as a monorepo with a presentation layer, an API layer, retrieval and rules modules, and a mock data package that simulates provider and insurance integrations.

## Flow

1. The user submits symptoms, insurance details, and a location.
2. The backend runs rule-based triage to infer urgency and care type.
3. Insurance data is normalized into a matched plan and coverage summary.
4. Doctor search loads nearby providers from mock data and applies specialty, insurance, distance, language, and trust scoring.
5. The frontend presents doctor cards, a ranking explanation, and booking actions.
6. Chat and document endpoints provide an explainable AI-style layer for demos.

## Components

- `apps/web`: Next.js app-router UI for the multi-step experience.
- `apps/api`: FastAPI app with routers, services, rules, and repositories.
- `packages/mock-data`: JSON fixtures used by repositories and tests.
- `infra`: Optional local support for Postgres and Qdrant if the project is extended.

## Extension points

- Replace mock repositories with SQLAlchemy-backed repositories.
- Replace deterministic AI stubs with OpenAI responses and Qdrant retrieval.
- Add auth, persistent chat sessions, and real calendar booking integrations.

