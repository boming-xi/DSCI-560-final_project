# API Contract

> Note: this file is a lightweight contract sketch. For the current product scope and live workflow status, use [current-state.md](/Users/boming/Downloads/DSCI-560-final_project/docs/current-state.md) as the primary reference.

Base URL: `http://localhost:8000/api/v1`

## Endpoints

- `GET /health`
- `POST /auth/demo-login`
- `POST /symptoms/triage`
- `POST /insurance/parse`
- `POST /doctors/search`
- `GET /doctors/{doctor_id}`
- `GET /booking/slots/{doctor_id}`
- `POST /booking/appointments`
- `POST /chat/message`
- `POST /documents/explain`

## Sample request: triage

```json
{
  "symptom_text": "I have had a sore throat and fever for three days",
  "duration_days": 3,
  "location": {
    "latitude": 34.0224,
    "longitude": -118.2851
  }
}
```

## Sample request: doctor search

```json
{
  "symptom_text": "sore throat and fever",
  "insurance_query": "Aetna USC student plan",
  "location": {
    "latitude": 34.0224,
    "longitude": -118.2851
  },
  "preferred_language": "Mandarin"
}
```
