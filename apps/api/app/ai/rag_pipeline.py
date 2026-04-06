from __future__ import annotations

from app.ai.embedding_client import EmbeddingClient
from app.retrieval.retriever import Retriever


class RAGPipeline:
    def __init__(self, embedding_client: EmbeddingClient) -> None:
        self.embedding_client = embedding_client

    def answer_from_document(self, question: str, document_text: str) -> list[str]:
        retriever = Retriever(self.embedding_client)
        retriever.index_document("uploaded-doc", document_text)
        return retriever.retrieve(question, top_k=2)
