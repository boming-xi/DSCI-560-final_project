from __future__ import annotations

DEFAULT_LATITUDE = 34.0224
DEFAULT_LONGITUDE = -118.2851


def coalesce_location(location: object | None) -> tuple[float, float]:
    if location is None:
        return DEFAULT_LATITUDE, DEFAULT_LONGITUDE
    latitude = getattr(location, "latitude", DEFAULT_LATITUDE)
    longitude = getattr(location, "longitude", DEFAULT_LONGITUDE)
    return latitude, longitude

