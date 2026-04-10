from __future__ import annotations

import mimetypes
from pathlib import Path

import fitz
from fastapi import HTTPException, status
from fastapi import UploadFile

from app.ai.embedding_client import EmbeddingClient
from app.ai.llm_client import LLMClient
from app.ai.ocr_client import OCRClient, OCRImageInput
from app.ai.medical_explainer import MedicalExplainer
from app.ai.rag_pipeline import RAGPipeline
from app.models.user import User
from app.retrieval.vector_store import VectorStore
from app.schemas.document import (
    DocumentExplainRequest,
    DocumentExplainResponse,
    DocumentExtractResponse,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SCANNED_TEXT_THRESHOLD = 80
MAX_OCR_PDF_PAGES = 6


class DocumentService:
    def __init__(
        self,
        llm_client: LLMClient,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        ocr_client: OCRClient,
    ) -> None:
        self.explainer = MedicalExplainer(llm_client=llm_client)
        self.rag_pipeline = RAGPipeline(
            embedding_client=embedding_client,
            vector_store=vector_store,
        )
        self.ocr_client = ocr_client

    async def extract_upload(
        self,
        current_user: User,
        uploaded_file: UploadFile,
        *,
        document_type: str = "medical_report",
        title: str | None = None,
    ) -> DocumentExtractResponse:
        del current_user
        file_bytes = await uploaded_file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Uploaded file is too large. Please keep files under 10 MB.",
            )

        source_file_name = uploaded_file.filename or "uploaded-document"
        source_mime_type = self._resolve_mime_type(uploaded_file.content_type, source_file_name)
        resolved_title = (title or Path(source_file_name).stem or "Uploaded document").strip()

        if self._is_text_file(source_mime_type, source_file_name):
            extracted_text = self._decode_text_file(file_bytes)
            return self._build_extract_response(
                title=resolved_title,
                document_type=document_type,
                source_file_name=source_file_name,
                source_mime_type=source_mime_type,
                extraction_method="text",
                extracted_text=extracted_text,
            )

        if self._is_pdf(source_mime_type, source_file_name):
            extracted_text, extraction_method, warnings = self._extract_pdf_text(
                file_bytes,
                fallback_title=resolved_title,
            )
            return self._build_extract_response(
                title=resolved_title,
                document_type=document_type,
                source_file_name=source_file_name,
                source_mime_type=source_mime_type,
                extraction_method=extraction_method,
                extracted_text=extracted_text,
                warnings=warnings,
            )

        if self._is_image(source_mime_type, source_file_name):
            extracted_text = self._extract_text_from_images(
                [
                    OCRImageInput(
                        mime_type=source_mime_type,
                        content=file_bytes,
                        label=source_file_name,
                    )
                ],
                prompt=(
                    "Extract all visible text from this document image. "
                    "Preserve important numbers, names, and section labels. "
                    "Return only the transcription."
                ),
            )
            return self._build_extract_response(
                title=resolved_title,
                document_type=document_type,
                source_file_name=source_file_name,
                source_mime_type=source_mime_type,
                extraction_method="image_ocr",
                extracted_text=extracted_text,
            )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Please upload text, PDF, PNG, JPG, JPEG, GIF, or WEBP files.",
        )

    def explain(self, current_user: User, request: DocumentExplainRequest) -> DocumentExplainResponse:
        try:
            context = self.rag_pipeline.prepare_document_context(
                user_id=current_user.id,
                question=request.focus_question,
                document_text=request.content,
                document_id=request.document_id,
                title=request.title,
                document_type=request.document_type,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        summary, important_terms = self.explainer.explain(
            context.document_text,
            supporting_chunks=context.supporting_chunks,
        )
        follow_up_questions = [
            "What does this result mean for my next appointment?",
            "Are any values outside the expected range for my situation?",
            "Should I repeat this test or monitor symptoms at home first?",
        ]
        if context.supporting_chunks:
            follow_up_questions.append("Can you help me interpret the highlighted section from the report?")
        return DocumentExplainResponse(
            document_id=context.document_id,
            indexed_now=context.indexed_now,
            vector_store_backend=context.vector_store_backend,
            supporting_chunks=context.supporting_chunks,
            summary=summary,
            important_terms=important_terms,
            follow_up_questions=follow_up_questions[:4],
            disclaimer="This explanation is educational and should be confirmed with a licensed clinician.",
        )

    def _extract_pdf_text(
        self,
        file_bytes: bytes,
        *,
        fallback_title: str,
    ) -> tuple[str, str, list[str]]:
        warnings: list[str] = []
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            page_texts = [page.get_text("text").strip() for page in pdf]
            extracted_text = "\n\n".join(text for text in page_texts if text).strip()
            if len(extracted_text) >= SCANNED_TEXT_THRESHOLD:
                return extracted_text, "pdf_text", warnings

            image_inputs: list[OCRImageInput] = []
            page_limit = min(pdf.page_count, MAX_OCR_PDF_PAGES)
            for index in range(page_limit):
                page = pdf[index]
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                image_inputs.append(
                    OCRImageInput(
                        mime_type="image/png",
                        content=pixmap.tobytes("png"),
                        label=f"{fallback_title}-page-{index + 1}",
                    )
                )
            if pdf.page_count > MAX_OCR_PDF_PAGES:
                warnings.append(
                    f"OCR was limited to the first {MAX_OCR_PDF_PAGES} pages to keep the upload responsive."
                )

            try:
                ocr_text = self._extract_text_from_images(
                    image_inputs,
                    prompt=(
                        "Extract all visible text from these PDF page images. "
                        "Preserve section breaks and numbers. "
                        "Return only the transcription."
                    ),
                )
            except HTTPException:
                if extracted_text:
                    warnings.append(
                        "OCR was unavailable, so this PDF uses the text that could be extracted directly."
                    )
                    return extracted_text, "pdf_text_partial", warnings
                raise
            if extracted_text and extracted_text not in ocr_text:
                warnings.append("This PDF looked partially scanned, so OCR was used to improve extraction.")
            return ocr_text or extracted_text, "pdf_ocr", warnings
        finally:
            pdf.close()

    def _extract_text_from_images(
        self,
        images: list[OCRImageInput],
        *,
        prompt: str,
    ) -> str:
        try:
            return self.ocr_client.extract_text_from_images(images, prompt=prompt)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

    @staticmethod
    def _resolve_mime_type(content_type: str | None, file_name: str) -> str:
        if content_type and content_type != "application/octet-stream":
            return content_type
        guessed_type, _ = mimetypes.guess_type(file_name)
        return guessed_type or "application/octet-stream"

    @staticmethod
    def _is_pdf(mime_type: str, file_name: str) -> bool:
        return mime_type == "application/pdf" or file_name.lower().endswith(".pdf")

    @staticmethod
    def _is_image(mime_type: str, file_name: str) -> bool:
        return mime_type.startswith("image/") or file_name.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp")
        )

    @staticmethod
    def _is_text_file(mime_type: str, file_name: str) -> bool:
        if mime_type.startswith("text/"):
            return True
        return file_name.lower().endswith((".txt", ".md", ".json", ".csv"))

    @staticmethod
    def _decode_text_file(file_bytes: bytes) -> str:
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return file_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="ignore").strip()

    @staticmethod
    def _build_extract_response(
        *,
        title: str,
        document_type: str,
        source_file_name: str,
        source_mime_type: str,
        extraction_method: str,
        extracted_text: str,
        warnings: list[str] | None = None,
    ) -> DocumentExtractResponse:
        cleaned_text = extracted_text.strip()
        if not cleaned_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="We could not extract readable text from this file.",
            )
        return DocumentExtractResponse(
            title=title,
            document_type=document_type,
            source_file_name=source_file_name,
            source_mime_type=source_mime_type,
            extraction_method=extraction_method,
            extracted_text=cleaned_text,
            extracted_preview=cleaned_text[:240],
            warnings=warnings or [],
        )
