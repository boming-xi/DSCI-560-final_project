from __future__ import annotations

from functools import lru_cache

from app.ai.embedding_client import (
    DemoEmbeddingClient,
    EmbeddingClient,
    OpenAIEmbeddingClient,
    ResilientEmbeddingClient,
)
from app.ai.llm_client import DemoLLMClient, LLMClient, OpenAILLMClient, ResilientLLMClient
from app.core.config import Settings, get_settings as load_settings
from app.repositories.booking_repo import BookingRepository
from app.repositories.chat_repo import ChatRepository
from app.repositories.doctor_repo import DoctorRepository
from app.repositories.insurance_repo import InsuranceRepository
from app.repositories.user_repo import UserRepository
from app.services.booking_service import BookingService
from app.services.chat_service import ChatService
from app.services.doctor_search_service import DoctorSearchService
from app.services.document_service import DocumentService
from app.services.insurance_service import InsuranceService
from app.services.ranking_service import RankingService
from app.services.triage_service import TriageService


@lru_cache
def get_settings() -> Settings:
    return load_settings()


@lru_cache
def get_user_repo() -> UserRepository:
    return UserRepository()


@lru_cache
def get_doctor_repo() -> DoctorRepository:
    return DoctorRepository(get_settings())


@lru_cache
def get_insurance_repo() -> InsuranceRepository:
    return InsuranceRepository(get_settings())


@lru_cache
def get_booking_repo() -> BookingRepository:
    return BookingRepository()


@lru_cache
def get_chat_repo() -> ChatRepository:
    return ChatRepository()


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    fallback = DemoLLMClient()
    if not settings.openai_api_key:
        return fallback
    return ResilientLLMClient(
        primary=OpenAILLMClient(
            api_key=settings.openai_api_key,
            model=settings.openai_chat_model,
            reasoning_effort=settings.openai_reasoning_effort,
            max_output_tokens=settings.openai_max_output_tokens,
        ),
        fallback=fallback,
    )


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    settings = get_settings()
    fallback = DemoEmbeddingClient()
    if not settings.openai_api_key:
        return fallback
    return ResilientEmbeddingClient(
        primary=OpenAIEmbeddingClient(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        ),
        fallback=fallback,
    )


@lru_cache
def get_triage_service() -> TriageService:
    return TriageService()


@lru_cache
def get_insurance_service() -> InsuranceService:
    return InsuranceService(get_insurance_repo())


@lru_cache
def get_ranking_service() -> RankingService:
    return RankingService()


@lru_cache
def get_doctor_search_service() -> DoctorSearchService:
    return DoctorSearchService(
        doctor_repo=get_doctor_repo(),
        insurance_repo=get_insurance_repo(),
        triage_service=get_triage_service(),
        insurance_service=get_insurance_service(),
        ranking_service=get_ranking_service(),
    )


@lru_cache
def get_booking_service() -> BookingService:
    return BookingService(get_doctor_repo(), get_booking_repo())


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(
        triage_service=get_triage_service(),
        insurance_service=get_insurance_service(),
        llm_client=get_llm_client(),
    )


@lru_cache
def get_document_service() -> DocumentService:
    return DocumentService(
        llm_client=get_llm_client(),
        embedding_client=get_embedding_client(),
    )
