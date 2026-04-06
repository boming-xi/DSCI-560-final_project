from __future__ import annotations

from app.ai.embedding_client import EmbeddingClient
from app.ai.llm_client import LLMClient
from app.ai.medical_explainer import MedicalExplainer
from app.ai.rag_pipeline import RAGPipeline
from app.schemas.document import DocumentExplainRequest, DocumentExplainResponse


class DocumentService:
    def __init__(self, llm_client: LLMClient, embedding_client: EmbeddingClient) -> None:
        self.explainer = MedicalExplainer(llm_client=llm_client)
        self.rag_pipeline = RAGPipeline(embedding_client=embedding_client)

    def explain(self, request: DocumentExplainRequest) -> DocumentExplainResponse:
        supporting_chunks = self.rag_pipeline.answer_from_document("What matters most?", request.content)
        summary, important_terms = self.explainer.explain(
            request.content,
            supporting_chunks=supporting_chunks,
        )
        follow_up_questions = [
            "What does this result mean for my next appointment?",
            "Are any values outside the expected range for my situation?",
            "Should I repeat this test or monitor symptoms at home first?",
        ]
        if supporting_chunks:
            follow_up_questions.append("Can you help me interpret the highlighted section from the report?")
        return DocumentExplainResponse(
            summary=summary,
            important_terms=important_terms,
            follow_up_questions=follow_up_questions[:4],
            disclaimer="This explanation is educational and should be confirmed with a licensed clinician.",
        )
