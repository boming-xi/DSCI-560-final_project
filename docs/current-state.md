# Current Project State

## Summary

The project is currently a multi-step healthcare navigation application that helps a user move from symptom description to insurance choice, doctor ranking, and official booking handoff. The frontend is built with Next.js App Router. The backend is built with FastAPI and exposes rule-driven triage, insurance guidance, doctor ranking, and provider handoff APIs.

## Active user flow

1. `Symptoms`
   The user describes symptoms, chooses a preferred language, and confirms a search location.
2. `Insurance`
   The user either uploads an existing insurance document or uses the insurance advisor to narrow plan options.
3. `Doctors`
   The backend ranks clinicians using specialty fit, insurance evidence, distance, availability, language, and trust signals. A shared-context group discussion helps the user make the final choice.
4. `Booking`
   The site does not book internally. It hands the user off to the provider's official booking page when a live link is available.

## Frontend state

- The old standalone chat page has been removed from the navigation.
- The doctor page now contains the final-choice group discussion room.
- Input fields use placeholder guidance rather than prefilled sample answers.
- Empty, loading, and handoff states have been rewritten to read like product copy instead of development prompts.
- The old in-app booking modal and confirmation path have been removed from the active frontend flow.

## Backend state

- Symptom triage is active.
- Insurance parsing is active.
- The insurance advisor is active and feeds doctor search.
- Doctor ranking is active.
- Official booking handoff is active.
- Provider directory verification supports live carrier clients when configured.

## Data and integration model

- The backend can use Postgres for persistent reference data.
- If Postgres is unavailable, the API falls back to local JSON reference files.
- The insurance advisor currently works against the California marketplace catalog used by this project.
- Doctor results are now official-first in the surfaced UI.
- Live provider-directory verification is supported when carrier-specific credentials and endpoints are configured.
- Live booking handoff is currently centered on the LA pilot provider set.

## Current boundaries

- The application does not hold or confirm appointment slots inside the site.
- Official carrier verification is only as strong as the configured provider-directory endpoint.
- Some backend support code still exists for broader AI/document workflows, but the current primary UI is focused on insurance-aware care navigation and official handoff rather than a general-purpose chat surface.

## Engineering notes

- Frontend stack: Next.js 14 App Router, React, TypeScript
- Backend stack: FastAPI, Pydantic, service/repository split
- Persistence: Postgres optional, JSON fallback supported
- Retrieval layer: available in the backend, but not the central UI surface of the current release

## What was cleaned up in this pass

- Removed an unused frontend booking modal
- Removed stale frontend API wrappers for in-app booking confirmation and unused chat/document calls
- Removed stale flow fields that no longer fit the current booking handoff model
- Updated product copy to match the current official-handoff experience
