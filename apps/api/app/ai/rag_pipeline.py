from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.ai.embedding_client import EmbeddingClient
from app.retrieval.vector_store import VectorStore
from app.retrieval.retriever import Retriever
from app.utils.parsers import normalize_text


@dataclass(slots=True)
class GroundedDocumentContext:
    document_id: str
    document_text: str
    supporting_chunks: list[str]
    indexed_now: bool
    vector_store_backend: str
    vector_namespace: str


class RAGPipeline:
    def __init__(self, embedding_client: EmbeddingClient, vector_store: VectorStore) -> None:
        self.embedding_client = embedding_client
        self.vector_store = vector_store

    def prepare_document_context(
        self,
        *,
        user_id: str,
        question: str,
        document_text: str | None,
        document_id: str | None = None,
        title: str | None = None,
        document_type: str = "medical_report",
    ) -> GroundedDocumentContext:
        retriever = Retriever(self.embedding_client, self.vector_store)
        resolved_document_id = document_id or self._build_document_id(
            user_id=user_id,
            title=title,
            document_type=document_type,
            document_text=document_text or "",
        )
        resolved_document_text = document_text or retriever.load_document_text(
            user_id=user_id,
            document_id=resolved_document_id,
        )
        if not resolved_document_text:
            raise ValueError("Document content was not provided and no stored document was found.")

        retrieval = retriever.retrieve_document(
            user_id=user_id,
            document_id=resolved_document_id,
            text=resolved_document_text,
            question=question,
            title=title,
            document_type=document_type,
            top_k=2,
        )
        return GroundedDocumentContext(
            document_id=resolved_document_id,
            document_text=resolved_document_text,
            supporting_chunks=retrieval.chunks,
            indexed_now=retrieval.indexed_now,
            vector_store_backend=self.vector_store.backend_name,
            vector_namespace=retrieval.vector_namespace,
        )

    @staticmethod
    def _build_document_id(
        *,
        user_id: str,
        title: str | None,
        document_type: str,
        document_text: str,
    ) -> str:
        digest = hashlib.sha256(
            "|".join(
                [
                    user_id,
                    normalize_text(title),
                    normalize_text(document_type),
                    normalize_text(document_text),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return f"doc-{digest[:16]}"
