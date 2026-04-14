from __future__ import annotations

import httpx


class CensusGeocoderClient:
    def __init__(self, base_url: str, benchmark: str = "Public_AR_Current", timeout_seconds: float = 15.0) -> None:
        self.base_url = base_url
        self.benchmark = benchmark
        self.timeout_seconds = timeout_seconds

    def geocode(self, address: str) -> tuple[float, float] | None:
        params = {
            "address": address,
            "benchmark": self.benchmark,
            "format": "json",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()

        matches = payload.get("result", {}).get("addressMatches", [])
        if not matches:
            return None
        coordinates = matches[0].get("coordinates") or {}
        x = coordinates.get("x")
        y = coordinates.get("y")
        if x is None or y is None:
            return None
        return float(y), float(x)
