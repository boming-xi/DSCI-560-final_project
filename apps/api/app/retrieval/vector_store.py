from __future__ import annotations

from math import sqrt


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(l * r for l, r in zip(left, right))
    left_norm = sqrt(sum(l * l for l in left))
    right_norm = sqrt(sum(r * r for r in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.items: list[tuple[str, list[float], dict[str, str]]] = []

    def upsert(self, item_id: str, vector: list[float], metadata: dict[str, str]) -> None:
        self.items = [item for item in self.items if item[0] != item_id]
        self.items.append((item_id, vector, metadata))

    def search(self, query_vector: list[float], top_k: int = 3) -> list[dict[str, object]]:
        ranked = sorted(
            (
                {
                    "id": item_id,
                    "score": cosine_similarity(query_vector, vector),
                    "metadata": metadata,
                }
                for item_id, vector, metadata in self.items
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        return ranked[:top_k]

