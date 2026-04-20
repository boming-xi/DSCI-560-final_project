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
    openai_ocr_model: str
    openai_reasoning_effort: str
    openai_max_output_tokens: int
    demo_users_file: Path
    demo_auth_secret: str
    postgres_url: str
    provider_directory_source: str
    provider_directory_snapshot_file: Path | None
    provider_directory_api_url: str | None
    provider_directory_api_key: str | None
    provider_directory_api_key_header: str
    provider_directory_timeout_seconds: float
    provider_directory_query_city: str | None
    provider_directory_query_state: str | None
    provider_directory_query_taxonomy: str | None
    provider_directory_query_limit: int
    provider_directory_geocoder_url: str
    provider_directory_geocoder_benchmark: str
    provider_directory_default_latitude: float
    provider_directory_default_longitude: float
    scheduling_source: str
    scheduling_snapshot_file: Path | None
    scheduling_api_url: str | None
    scheduling_api_key: str | None
    scheduling_api_key_header: str
    scheduling_timeout_seconds: float
    scheduling_slot_stale_hours: int
    scheduling_fhir_count: int
    qdrant_url: str
    qdrant_local_path: Path
    qdrant_collection_prefix: str
    project_root: Path
    reference_data_dir: Path


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
        openai_ocr_model=os.getenv(
            "OPENAI_OCR_MODEL",
            os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini"),
        ),
        openai_reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "low"),
        openai_max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700")),
        demo_users_file=Path(os.getenv("DEMO_USERS_FILE", str(default_demo_users_file))),
        demo_auth_secret=os.getenv("DEMO_AUTH_SECRET", "change-me-in-demo"),
        postgres_url=os.getenv(
            "POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/ai_healthcare"
        ),
        provider_directory_source=os.getenv("PROVIDER_DIRECTORY_SOURCE", "snapshot"),
        provider_directory_snapshot_file=(
            Path(snapshot_file)
            if (snapshot_file := os.getenv("PROVIDER_DIRECTORY_SNAPSHOT_FILE"))
            else None
        ),
        provider_directory_api_url=os.getenv("PROVIDER_DIRECTORY_API_URL") or None,
        provider_directory_api_key=os.getenv("PROVIDER_DIRECTORY_API_KEY") or None,
        provider_directory_api_key_header=os.getenv(
            "PROVIDER_DIRECTORY_API_KEY_HEADER", "Authorization"
        ),
        provider_directory_timeout_seconds=float(
            os.getenv("PROVIDER_DIRECTORY_TIMEOUT_SECONDS", "15")
        ),
        provider_directory_query_city=os.getenv("PROVIDER_DIRECTORY_QUERY_CITY") or None,
        provider_directory_query_state=os.getenv("PROVIDER_DIRECTORY_QUERY_STATE") or None,
        provider_directory_query_taxonomy=os.getenv("PROVIDER_DIRECTORY_QUERY_TAXONOMY") or None,
        provider_directory_query_limit=int(os.getenv("PROVIDER_DIRECTORY_QUERY_LIMIT", "25")),
        provider_directory_geocoder_url=os.getenv(
            "PROVIDER_DIRECTORY_GEOCODER_URL",
            "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress",
        ),
        provider_directory_geocoder_benchmark=os.getenv(
            "PROVIDER_DIRECTORY_GEOCODER_BENCHMARK", "Public_AR_Current"
        ),
        provider_directory_default_latitude=float(
            os.getenv("PROVIDER_DIRECTORY_DEFAULT_LATITUDE", "34.0224")
        ),
        provider_directory_default_longitude=float(
            os.getenv("PROVIDER_DIRECTORY_DEFAULT_LONGITUDE", "-118.2851")
        ),
        scheduling_source=os.getenv("SCHEDULING_SOURCE", "snapshot"),
        scheduling_snapshot_file=(
            Path(schedule_snapshot_file)
            if (schedule_snapshot_file := os.getenv("SCHEDULING_SNAPSHOT_FILE"))
            else None
        ),
        scheduling_api_url=os.getenv("SCHEDULING_API_URL") or None,
        scheduling_api_key=os.getenv("SCHEDULING_API_KEY") or None,
        scheduling_api_key_header=os.getenv("SCHEDULING_API_KEY_HEADER", "Authorization"),
        scheduling_timeout_seconds=float(os.getenv("SCHEDULING_TIMEOUT_SECONDS", "15")),
        scheduling_slot_stale_hours=int(os.getenv("SCHEDULING_SLOT_STALE_HOURS", "24")),
        scheduling_fhir_count=int(os.getenv("SCHEDULING_FHIR_COUNT", "50")),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_local_path=Path(
            os.getenv(
                "QDRANT_LOCAL_PATH",
                str(project_root / "apps" / "api" / "data" / "qdrant_local"),
            )
        ),
        qdrant_collection_prefix=os.getenv("QDRANT_COLLECTION_PREFIX", "documents"),
        project_root=project_root,
        reference_data_dir=project_root / "packages" / "reference-data",
    )
