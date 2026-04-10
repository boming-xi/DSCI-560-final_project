from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    api_host: str
    api_port: int
    cors_origins: list[str]
    openai_api_key: str | None
    openai_chat_model: str
    openai_embedding_model: str
    openai_reasoning_effort: str
    openai_max_output_tokens: int
    demo_users_file: Path
    demo_auth_secret: str
    postgres_url: str
    qdrant_url: str
    project_root: Path
    mock_data_dir: Path


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[4]
    load_dotenv(project_root / ".env")
    default_demo_users_file = project_root / "apps" / "api" / "data" / "demo_users.json"
    return Settings(
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000")),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini"),
        openai_embedding_model=os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        openai_reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "low"),
        openai_max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700")),
        demo_users_file=Path(os.getenv("DEMO_USERS_FILE", str(default_demo_users_file))),
        demo_auth_secret=os.getenv("DEMO_AUTH_SECRET", "change-me-in-demo"),
        postgres_url=os.getenv(
            "POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/ai_healthcare"
        ),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        project_root=project_root,
        mock_data_dir=project_root / "packages" / "mock-data",
    )
