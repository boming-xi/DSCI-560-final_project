from __future__ import annotations

from app.ai.embedding_client import EmbeddingClient
from app.retrieval.chunking import chunk_text
from app.retrieval.vector_store import InMemoryVectorStore


class Retriever:
    def __init__(self, embedding_client: EmbeddingClient) -> None:
        self.embedding_client = embedding_client
        self.vector_store = InMemoryVectorStore()

    def index_document(self, document_id: str, text: str) -> None:
        for idx, chunk in enumerate(chunk_text(text)):
            item_id = f"{document_id}:{idx}"
            self.vector_store.upsert(
                item_id,
                self.embedding_client.embed_text(chunk),
                {"chunk": chunk},
            )

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        results = self.vector_store.search(self.embedding_client.embed_text(query), top_k=top_k)
        return [str(result["metadata"]["chunk"]) for result in results if result["score"] > 0]
