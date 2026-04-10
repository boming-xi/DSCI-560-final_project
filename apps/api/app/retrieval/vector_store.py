from __future__ import annotations

from dataclasses import dataclass
import logging
from math import sqrt
from pathlib import Path
import re
from typing import Protocol, Sequence
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)

PayloadValue = str | int | float | bool


@dataclass(slots=True)
class VectorRecord:
    item_id: str
    vector: list[float]
    metadata: dict[str, PayloadValue]


@dataclass(slots=True)
class VectorSearchResult:
    item_id: str
    score: float
    metadata: dict[str, PayloadValue]


class VectorStore(Protocol):
    backend_name: str

    def upsert_many(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        ...

    def search(
        self,
        namespace: str,
        query_vector: list[float],
        *,
        filters: dict[str, PayloadValue] | None = None,
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[VectorSearchResult]:
        ...

    def has_records(self, namespace: str, filters: dict[str, PayloadValue]) -> bool:
        ...

    def list_payloads(
        self,
        namespace: str,
        *,
        filters: dict[str, PayloadValue] | None = None,
        limit: int = 256,
    ) -> list[dict[str, PayloadValue]]:
        ...

    def list_namespaces(self) -> list[str]:
        ...

    def close(self) -> None:
        ...


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(l * r for l, r in zip(left, right))
    left_norm = sqrt(sum(l * l for l in left))
    right_norm = sqrt(sum(r * r for r in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _matches_filters(
    metadata: dict[str, PayloadValue],
    filters: dict[str, PayloadValue] | None,
) -> bool:
    if not filters:
        return True
    return all(metadata.get(key) == value for key, value in filters.items())


def _normalize_namespace(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return normalized.strip("_") or "default"


class InMemoryVectorStore:
    backend_name = "memory"

    def __init__(self) -> None:
        self.items_by_namespace: dict[str, list[tuple[str, list[float], dict[str, PayloadValue]]]] = {}

    def upsert_many(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        current_items = self.items_by_namespace.setdefault(namespace, [])
        filtered_items = [item for item in current_items if item[0] not in {record.item_id for record in records}]
        filtered_items.extend((record.item_id, record.vector, record.metadata) for record in records)
        self.items_by_namespace[namespace] = filtered_items

    def search(
        self,
        namespace: str,
        query_vector: list[float],
        *,
        filters: dict[str, PayloadValue] | None = None,
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[VectorSearchResult]:
        ranked = sorted(
            (
                VectorSearchResult(
                    item_id=item_id,
                    score=cosine_similarity(query_vector, vector),
                    metadata=metadata,
                )
                for item_id, vector, metadata in self.items_by_namespace.get(namespace, [])
                if _matches_filters(metadata, filters)
            ),
            key=lambda item: item.score,
            reverse=True,
        )
        if score_threshold is None:
            return ranked[:top_k]
        return [item for item in ranked if item.score >= score_threshold][:top_k]

    def has_records(self, namespace: str, filters: dict[str, PayloadValue]) -> bool:
        return any(
            _matches_filters(metadata, filters)
            for _, _, metadata in self.items_by_namespace.get(namespace, [])
        )

    def list_payloads(
        self,
        namespace: str,
        *,
        filters: dict[str, PayloadValue] | None = None,
        limit: int = 256,
    ) -> list[dict[str, PayloadValue]]:
        payloads = [
            metadata
            for _, _, metadata in self.items_by_namespace.get(namespace, [])
            if _matches_filters(metadata, filters)
        ]
        return payloads[:limit]

    def list_namespaces(self) -> list[str]:
        return list(self.items_by_namespace.keys())

    def close(self) -> None:
        return None


class QdrantVectorStore:
    def __init__(
        self,
        client: QdrantClient,
        *,
        base_collection_prefix: str,
        backend_name: str,
    ) -> None:
        self.client = client
        self.base_collection_prefix = _normalize_namespace(base_collection_prefix)
        self.backend_name = backend_name
        self._known_collections: set[str] = set()

    @classmethod
    def create(
        cls,
        *,
        qdrant_url: str | None,
        local_path: Path,
        base_collection_prefix: str,
    ) -> QdrantVectorStore:
        if qdrant_url:
            try:
                remote_client = QdrantClient(
                    url=qdrant_url,
                    timeout=2,
                    check_compatibility=False,
                )
                remote_client.get_collections()
                return cls(
                    remote_client,
                    base_collection_prefix=base_collection_prefix,
                    backend_name="qdrant-remote",
                )
            except Exception as exc:
                logger.warning(
                    "Remote Qdrant unavailable at %s, falling back to local persistent store: %s",
                    qdrant_url,
                    exc,
                )

        local_path.mkdir(parents=True, exist_ok=True)
        local_client = QdrantClient(path=str(local_path))
        return cls(
            local_client,
            base_collection_prefix=base_collection_prefix,
            backend_name="qdrant-local",
        )

    def upsert_many(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        if not records:
            return

        collection_name = self._collection_name(namespace)
        self._ensure_collection(collection_name, vector_size=len(records[0].vector))
        points = [
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, record.item_id)),
                vector=record.vector,
                payload=record.metadata,
            )
            for record in records
        ]
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def search(
        self,
        namespace: str,
        query_vector: list[float],
        *,
        filters: dict[str, PayloadValue] | None = None,
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[VectorSearchResult]:
        collection_name = self._collection_name(namespace)
        if not self.client.collection_exists(collection_name):
            return []

        response = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=self._build_filter(filters),
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold,
        )
        return [
            VectorSearchResult(
                item_id=str(point.id),
                score=float(point.score or 0.0),
                metadata=dict(point.payload or {}),
            )
            for point in response.points
        ]

    def has_records(self, namespace: str, filters: dict[str, PayloadValue]) -> bool:
        collection_name = self._collection_name(namespace)
        if not self.client.collection_exists(collection_name):
            return False

        records, _ = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=self._build_filter(filters),
            with_payload=True,
            with_vectors=False,
            limit=1,
        )
        return bool(records)

    def list_payloads(
        self,
        namespace: str,
        *,
        filters: dict[str, PayloadValue] | None = None,
        limit: int = 256,
    ) -> list[dict[str, PayloadValue]]:
        collection_name = self._collection_name(namespace)
        if not self.client.collection_exists(collection_name):
            return []

        records, _ = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=self._build_filter(filters),
            with_payload=True,
            with_vectors=False,
            limit=limit,
        )
        return [dict(record.payload or {}) for record in records]

    def list_namespaces(self) -> list[str]:
        prefix = f"{self.base_collection_prefix}__"
        return [
            collection.name.removeprefix(prefix)
            for collection in self.client.get_collections().collections
            if collection.name.startswith(prefix)
        ]

    def close(self) -> None:
        self.client.close()

    def _collection_name(self, namespace: str) -> str:
        return f"{self.base_collection_prefix}__{_normalize_namespace(namespace)}"

    def _ensure_collection(self, collection_name: str, *, vector_size: int) -> None:
        if collection_name in self._known_collections:
            return
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
                on_disk_payload=True,
            )
        self._known_collections.add(collection_name)

    @staticmethod
    def _build_filter(filters: dict[str, PayloadValue] | None) -> models.Filter | None:
        if not filters:
            return None
        return models.Filter(
            must=[
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                )
                for key, value in filters.items()
            ]
        )
