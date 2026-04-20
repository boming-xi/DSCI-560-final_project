"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

import type { Location } from "@/lib/types";

const LeafletLocationMap = dynamic(
  () =>
    import("@/components/LeafletLocationMap").then(
      (module) => module.LeafletLocationMap,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="location-map-shell">
        <div className="location-map-skeleton">Preparing location tools...</div>
      </div>
    ),
  },
);

type LocationPickerProps = {
  value: Location;
  onChange: (location: Location) => void;
  autoLocateOnMount?: boolean;
};

function normalizeCoordinate(value: number): number {
  return Number(value.toFixed(6));
}

function getBrowserLocationError(error: GeolocationPositionError): string {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return "Location permission was denied. You can still click the map to choose where to search.";
    case error.POSITION_UNAVAILABLE:
      return "Your device could not determine a location just now. Try again or place the pin manually.";
    case error.TIMEOUT:
      return "Location lookup took too long. Try again or choose a point on the map.";
    default:
      return "We could not get your location right now. You can still place the pin manually.";
  }
}

export function LocationPicker({
  value,
  onChange,
  autoLocateOnMount = false,
}: LocationPickerProps) {
  const hasTriedAutoLocate = useRef(false);
  const [isLocating, setIsLocating] = useState(false);
  const [helperText, setHelperText] = useState(
    autoLocateOnMount
      ? "Looking up your current location to center the search area..."
      : "Use your browser location or click the map to place the search area.",
  );
  const [error, setError] = useState("");

  function setNextLocation(nextLocation: Location, message?: string) {
    onChange({
      latitude: normalizeCoordinate(nextLocation.latitude),
      longitude: normalizeCoordinate(nextLocation.longitude),
    });
    setError("");
    setHelperText(
      message ?? "Location updated. You can drag the pin or click the map to refine the search area.",
    );
  }

  function requestCurrentLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setError(
        "This browser does not support automatic location. Please use the map to choose your search area.",
      );
      setHelperText("Pick a point on the map to continue.");
      return;
    }

    setIsLocating(true);
    setError("");
    setHelperText("Requesting your current location...");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setIsLocating(false);
        setNextLocation(
          {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
          "Using your current location. You can still drag the pin to adjust it.",
        );
      },
      (positionError) => {
        setIsLocating(false);
        setError(getBrowserLocationError(positionError));
        setHelperText("Click the map to keep moving.");
      },
      {
        enableHighAccuracy: true,
        maximumAge: 300000,
        timeout: 10000,
      },
    );
  }

  useEffect(() => {
    if (!autoLocateOnMount || hasTriedAutoLocate.current) {
      return;
    }

    hasTriedAutoLocate.current = true;
    requestCurrentLocation();
  }, [autoLocateOnMount]);

  return (
    <section className="location-section">
      <div className="location-toolbar">
        <div className="location-copy">
          <h3>Location</h3>
          <p>
            We use your location to find nearby clinics and rank doctors more
            accurately.
          </p>
        </div>
        <button
          className="button button-secondary"
          disabled={isLocating}
          onClick={requestCurrentLocation}
          type="button"
        >
          {isLocating ? "Locating..." : "Use my current location"}
        </button>
      </div>

      <LeafletLocationMap location={value} onChange={setNextLocation} />

      <p className="location-status">
        The current pin sets the search area used for nearby doctor ranking.
        Click the map or drag the pin to adjust it.
      </p>

      {error ? <p className="error-text">{error}</p> : null}
      {!error ? <p className="location-helper-text">{helperText}</p> : null}
    </section>
  );
}
