from __future__ import annotations

from dataclasses import dataclass

from app.ai.embedding_client import EmbeddingClient
from app.retrieval.chunking import chunk_text
from app.retrieval.vector_store import VectorRecord, VectorStore


@dataclass(slots=True)
class RetrievalResult:
    chunks: list[str]
    indexed_now: bool
    vector_namespace: str


class Retriever:
    def __init__(self, embedding_client: EmbeddingClient, vector_store: VectorStore) -> None:
        self.embedding_client = embedding_client
        self.vector_store = vector_store

    def retrieve_document(
        self,
        *,
        user_id: str,
        document_id: str,
        text: str,
        question: str,
        title: str | None = None,
        document_type: str = "medical_report",
        top_k: int = 3,
    ) -> RetrievalResult:
        query_vector, vector_namespace = self._embed_text(question)
        indexed_now = False

        if not self.vector_store.has_records(
            vector_namespace,
            {"user_id": user_id, "document_id": document_id},
        ):
            indexed_now = True
            document_chunks = chunk_text(text)
            chunk_vectors, chunk_namespace = self._embed_chunks(document_chunks)
            if chunk_namespace != vector_namespace:
                query_vector, vector_namespace = self._embed_text(question)
                if chunk_namespace != vector_namespace:
                    chunk_vectors, chunk_namespace = self._embed_chunks(document_chunks)
                if chunk_namespace != vector_namespace:
                    raise RuntimeError("Unable to stabilize document embeddings for retrieval.")

            self.vector_store.upsert_many(
                vector_namespace,
                [
                    VectorRecord(
                        item_id=f"{user_id}:{document_id}:{idx}",
                        vector=vector,
                        metadata={
                            "user_id": user_id,
                            "document_id": document_id,
                            "document_title": title or "Untitled document",
                            "document_type": document_type,
                            "chunk": chunk,
                            "chunk_index": idx,
                            "chunk_count": len(document_chunks),
                        },
                    )
                    for idx, (chunk, vector) in enumerate(zip(document_chunks, chunk_vectors))
                ],
            )

        results = self.vector_store.search(
            vector_namespace,
            query_vector,
            filters={"user_id": user_id, "document_id": document_id},
            top_k=top_k,
            score_threshold=0,
        )
        return RetrievalResult(
            chunks=[str(result.metadata["chunk"]) for result in results if result.metadata.get("chunk")],
            indexed_now=indexed_now,
            vector_namespace=vector_namespace,
        )

    def load_document_text(self, *, user_id: str, document_id: str) -> str | None:
        for namespace in self.vector_store.list_namespaces():
            payloads = self.vector_store.list_payloads(
                namespace,
                filters={"user_id": user_id, "document_id": document_id},
                limit=512,
            )
            if payloads:
                ordered_chunks = sorted(
                    payloads,
                    key=lambda payload: int(payload.get("chunk_index", 0)),
                )
                return " ".join(str(payload["chunk"]) for payload in ordered_chunks if payload.get("chunk"))
        return None

    def _embed_text(self, text: str) -> tuple[list[float], str]:
        vector = self.embedding_client.embed_text(text)
        return vector, self._namespace_for_vector(vector)

    def _embed_chunks(self, chunks: list[str]) -> tuple[list[list[float]], str]:
        vectors: list[list[float]] = []
        namespace: str | None = None

        for chunk in chunks:
            vector, current_namespace = self._embed_text(chunk)
            if namespace is None:
                namespace = current_namespace
            elif current_namespace != namespace:
                restart_vectors = [self.embedding_client.embed_text(existing_chunk) for existing_chunk in chunks]
                restart_namespace = self._namespace_for_vector(restart_vectors[0])
                if any(self._namespace_for_vector(vector) != restart_namespace for vector in restart_vectors[1:]):
                    raise RuntimeError("Embedding provider changed multiple times during indexing.")
                return restart_vectors, restart_namespace
            vectors.append(vector)

        if namespace is None:
            return [[0.0]], "default_1d"
        return vectors, namespace

    def _namespace_for_vector(self, vector: list[float]) -> str:
        provider_name = getattr(self.embedding_client, "provider_name", "embedding")
        return f"{provider_name}_{len(vector)}d"
