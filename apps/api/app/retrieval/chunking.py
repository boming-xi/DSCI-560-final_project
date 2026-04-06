from __future__ import annotations

from app.utils.parsers import sentence_split


def chunk_text(text: str, max_sentences: int = 2) -> list[str]:
    sentences = sentence_split(text)
    chunks: list[str] = []
    for index in range(0, len(sentences), max_sentences):
        chunks.append(" ".join(sentences[index : index + max_sentences]))
    return chunks or [text]

