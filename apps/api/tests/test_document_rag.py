from pathlib import Path

from app.ai.embedding_client import DemoEmbeddingClient
from app.ai.llm_client import DemoLLMClient
from app.ai.ocr_client import DemoOCRClient
from app.models.user import User
from app.retrieval.vector_store import QdrantVectorStore
from app.schemas.document import DocumentExplainRequest
from app.services.document_service import DocumentService


def _build_document_service(storage_path: Path) -> DocumentService:
    vector_store = QdrantVectorStore.create(
        qdrant_url=None,
        local_path=storage_path,
        base_collection_prefix="test_documents",
    )
    return DocumentService(
        llm_client=DemoLLMClient(),
        embedding_client=DemoEmbeddingClient(),
        vector_store=vector_store,
        ocr_client=DemoOCRClient(),
    )


def test_document_service_reuses_persisted_qdrant_index_across_instances(tmp_path: Path) -> None:
    storage_path = tmp_path / "qdrant_local"
    user = User(
        id="user-1",
        name="Test User",
        email="test@example.com",
    )

    first_service = _build_document_service(storage_path)
    first_response = first_service.explain(
        user,
        DocumentExplainRequest(
            title="CBC note",
            content=(
                "CBC result shows WBC slightly elevated. "
                "Mild inflammation noted. "
                "Follow up if fever persists."
            ),
            document_type="lab_report",
        ),
    )
    first_service.rag_pipeline.vector_store.close()

    second_service = _build_document_service(storage_path)
    second_response = second_service.explain(
        user,
        DocumentExplainRequest(
            document_id=first_response.document_id,
            focus_question="What matters most here?",
        ),
    )
    second_service.rag_pipeline.vector_store.close()

    assert first_response.document_id.startswith("doc-")
    assert first_response.indexed_now is True
    assert first_response.supporting_chunks
    assert second_response.document_id == first_response.document_id
    assert second_response.indexed_now is False
    assert second_response.supporting_chunks
    assert second_response.vector_store_backend == "qdrant-local"
