from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

DEMO_TOKEN = "demo-token"
PASSWORD_ITERATIONS = 200_000


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict[str, str]:
    if authorization is None:
        return {"id": "guest-user", "role": "guest"}
    if authorization == f"Bearer {DEMO_TOKEN}":
        return {"id": "demo-user", "role": "demo"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid demo token.",
    )


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    resolved_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        resolved_salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    )
    return digest.hex(), resolved_salt


def verify_password(password: str, password_hash: str, password_salt: str) -> bool:
    candidate_hash, _ = hash_password(password, salt=password_salt)
    return hmac.compare_digest(candidate_hash, password_hash)


def create_access_token(payload: dict[str, str], secret: str) -> str:
    encoded_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8")
    signature = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"demo.{encoded_payload}.{signature}"


def decode_access_token(token: str, secret: str) -> dict[str, str] | None:
    try:
        prefix, encoded_payload, signature = token.split(".", 2)
    except ValueError:
        return None
    if prefix != "demo":
        return None

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        return None

    try:
        payload_raw = base64.urlsafe_b64decode(encoded_payload.encode("utf-8"))
        payload = json.loads(payload_raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    return {str(key): str(value) for key, value in payload.items()}
