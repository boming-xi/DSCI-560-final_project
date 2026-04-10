from io import BytesIO

import fitz
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _demo_auth_headers() -> dict[str, str]:
    response = client.post("/api/v1/auth/demo-login", json={})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_document_extract_requires_authentication() -> None:
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("note.txt", b"Policy Aetna PPO", "text/plain")},
        data={"document_type": "insurance_document"},
    )
    assert response.status_code == 401


def test_document_extract_reads_uploaded_text_file() -> None:
    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("note.txt", b"Policy Aetna PPO student health", "text/plain")},
        data={"document_type": "insurance_document"},
        headers=_demo_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction_method"] == "text"
    assert "Aetna PPO" in payload["extracted_text"]


def test_document_extract_reads_uploaded_pdf() -> None:
    pdf = fitz.open()
    try:
        page = pdf.new_page()
        page.insert_text((72, 72), "CBC result shows WBC slightly elevated.")
        pdf_bytes = pdf.tobytes()
    finally:
        pdf.close()

    response = client.post(
        "/api/v1/documents/extract",
        files={"file": ("cbc.pdf", BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "lab_report"},
        headers=_demo_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction_method"] in {"pdf_text", "pdf_text_partial"}
    assert "WBC slightly elevated" in payload["extracted_text"]
