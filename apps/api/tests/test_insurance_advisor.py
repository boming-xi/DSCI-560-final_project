from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _demo_auth_headers() -> dict[str, str]:
    response = client.post("/api/v1/auth/demo-login", json={})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_insurance_advisor_requires_authentication() -> None:
    response = client.post(
        "/api/v1/insurance/advisor/message",
        json={"message": "I need help choosing insurance.", "conversation": []},
    )
    assert response.status_code == 401


def test_insurance_advisor_recommends_official_marketplace_plan_for_usc_area_profile() -> None:
    response = client.post(
        "/api/v1/insurance/advisor/message",
        json={
            "message": (
                "I am a USC student in California 90007. My budget is around $350 per month, "
                "I need regular prescriptions, and I do not want referrals if possible."
            ),
            "conversation": [],
        },
        headers=_demo_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["coverage_channel"] == "student"
    assert payload["readiness_label"] == "recommended"
    assert payload["recommendations"]
    assert payload["recommendations"][0]["plan_id"] != "usc-aetna-student"
    assert payload["recommendations"][0]["provider"] in {
        "Blue Shield of California",
        "Health Net",
        "Kaiser Permanente",
        "L.A. Care",
        "Molina Healthcare",
    }
    assert payload["recommendations"][0]["purchase_url"]
    assert payload["recommendations"][0]["purchase_url"] == "https://www.coveredca.com/"


def test_insurance_advisor_uses_real_marketplace_catalog_for_budget_case() -> None:
    response = client.post(
        "/api/v1/insurance/advisor/message",
        json={
            "message": (
                "I need a Covered California marketplace plan in 90007. "
                "I am 24, healthy, my budget is around $220 per month, and referrals are okay."
            ),
            "conversation": [],
        },
        headers=_demo_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["coverage_channel"] == "marketplace"
    assert payload["recommendations"]
    top = payload["recommendations"][0]
    assert top["provider"] in {
        "Health Net",
        "Kaiser Permanente",
        "Blue Shield of California",
        "L.A. Care",
        "Molina Healthcare",
    }
    assert top["purchase_url"] == "https://www.coveredca.com/"
    assert top["source_url"]
    assert top["plan_id"]
    assert top["monthly_premium_amount"] is not None


def test_doctor_search_accepts_plan_override_for_marketplace_recommendations() -> None:
    response = client.post(
        "/api/v1/doctors/search",
        json={
            "symptom_text": "sore throat and fever",
            "insurance_query": "Health Net Minimum Coverage Ambetter PPO",
            "insurance_selected_plan_id": "70285CA8040016",
            "location": {"latitude": 34.0224, "longitude": -118.2851},
            "preferred_language": "Mandarin",
            "duration_days": 3,
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["insurance_summary"]["matched"] is True
    assert payload["insurance_summary"]["plan_id"] == "70285CA8040016"
    assert payload["doctors"]
