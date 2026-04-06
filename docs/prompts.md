# Prompt Strategy

The current backend uses deterministic response templates, but the prompt design below shows how the project can evolve into an LLM-backed assistant.

## Triage prompt

- Extract main symptoms, duration, risk modifiers, and urgency cues.
- Return the likely care type, urgency band, and one-sentence rationale.
- Always include a safety disclaimer when symptoms imply emergency care.

## Insurance prompt

- Normalize the insurance provider and plan name from noisy user text or OCR output.
- Explain referral requirements and out-of-pocket expectations in plain language.

## Medical explainer prompt

- Rewrite uploaded medical terms in patient-friendly language.
- Highlight what the result might mean, what to ask a clinician, and when to seek faster care.
- Avoid making a diagnosis or prescribing medication.

