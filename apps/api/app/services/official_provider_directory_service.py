from __future__ import annotations

import logging
import os
from functools import cached_property
from typing import Any

import httpx

from app.core.config import Settings
from app.integrations.provider_directory_verification.base import (
    OfficialDirectoryMatch,
    ProviderDirectoryVerificationClient,
)
from app.integrations.provider_directory_verification.fhir_client import (
    FHIRProviderDirectoryVerificationClient,
)
from app.integrations.provider_directory_verification.json_client import (
    JSONProviderDirectoryVerificationClient,
)
from app.models.doctor import ClinicRecord, DoctorRecord
from app.utils.parsers import normalize_text

logger = logging.getLogger(__name__)


class OfficialProviderDirectoryService:
    _CARRIER_CONFIG = (
        ("aetna", "AETNA", "Aetna", ("aetna",)),
        ("anthem", "ANTHEM", "Anthem Blue Cross", ("anthem", "anthem blue cross")),
        (
            "blue_shield",
            "BLUE_SHIELD",
            "Blue Shield of California",
            ("blue shield", "blueshield"),
        ),
        ("cigna", "CIGNA", "Cigna", ("cigna",)),
        ("health_net", "HEALTH_NET", "Health Net", ("health net",)),
        ("kaiser", "KAISER", "Kaiser Permanente", ("kaiser", "kaiser permanente")),
        (
            "unitedhealthcare",
            "UNITEDHEALTHCARE",
            "UnitedHealthcare",
            ("unitedhealthcare", "united healthcare", "uhc"),
        ),
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.timeout_seconds = float(
            os.getenv(
                "OFFICIAL_PROVIDER_DIRECTORY_TIMEOUT_SECONDS",
                str(settings.provider_directory_timeout_seconds),
            )
        )

    @cached_property
    def clients(self) -> dict[str, ProviderDirectoryVerificationClient]:
        clients: dict[str, ProviderDirectoryVerificationClient] = {}
        for carrier_key, env_prefix, source_label, _aliases in self._CARRIER_CONFIG:
            client = self._client_from_env(env_prefix=env_prefix, source_label=source_label)
            if client is not None:
                clients[carrier_key] = client
        return clients

    def has_live_client(self, plan_context: Any) -> bool:
        carrier_key = self._carrier_key(getattr(plan_context, "provider", None))
        return bool(carrier_key and carrier_key in self.clients)

    def verify(
        self,
        *,
        plan_context: Any,
        doctor: DoctorRecord,
        clinic: ClinicRecord,
    ) -> OfficialDirectoryMatch | None:
        carrier_key = self._carrier_key(getattr(plan_context, "provider", None))
        if not carrier_key:
            return None
        client = self.clients.get(carrier_key)
        if client is None:
            return None
        try:
            return client.verify(plan_context=plan_context, doctor=doctor, clinic=clinic)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "Official provider directory verification failed for %s: %s",
                carrier_key,
                exc,
            )
            return None

    def _carrier_key(self, provider_name: str | None) -> str | None:
        normalized_provider = normalize_text(provider_name)
        if not normalized_provider:
            return None
        for carrier_key, _env_prefix, _label, aliases in self._CARRIER_CONFIG:
            if any(alias in normalized_provider for alias in aliases):
                return carrier_key
        return None

    def _client_from_env(
        self,
        *,
        env_prefix: str,
        source_label: str,
    ) -> ProviderDirectoryVerificationClient | None:
        url = os.getenv(f"{env_prefix}_PROVIDER_DIRECTORY_API_URL") or None
        if not url:
            return None
        api_type = (os.getenv(f"{env_prefix}_PROVIDER_DIRECTORY_API_TYPE", "fhir") or "fhir").lower()
        api_key = os.getenv(f"{env_prefix}_PROVIDER_DIRECTORY_API_KEY") or None
        api_key_header = os.getenv(
            f"{env_prefix}_PROVIDER_DIRECTORY_API_KEY_HEADER",
            "Authorization",
        )
        api_key_query_param = os.getenv(
            f"{env_prefix}_PROVIDER_DIRECTORY_API_KEY_QUERY_PARAM"
        ) or None

        if api_type == "json":
            return JSONProviderDirectoryVerificationClient(
                url=url,
                source_label=source_label,
                timeout_seconds=self.timeout_seconds,
                api_key=api_key,
                api_key_header=api_key_header,
                api_key_query_param=api_key_query_param,
            )
        return FHIRProviderDirectoryVerificationClient(
            base_url=url,
            source_label=source_label,
            timeout_seconds=self.timeout_seconds,
            api_key=api_key,
            api_key_header=api_key_header,
            api_key_query_param=api_key_query_param,
        )
