from __future__ import annotations

RANKING_WEIGHTS = {
    "specialty": 0.28,
    "insurance": 0.24,
    "distance": 0.16,
    "availability": 0.14,
    "language": 0.08,
    "trust": 0.10,
}


def combine_scores(scores: dict[str, float]) -> float:
    weighted_total = 0.0
    for key, weight in RANKING_WEIGHTS.items():
        weighted_total += scores.get(key, 0.0) * weight
    return round(weighted_total * 100, 1)

