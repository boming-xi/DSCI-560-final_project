"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

import { useTranslation } from "@/lib/LanguageProvider";
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
        <div className="location-map-skeleton" />
      </div>
    ),
  },
);

type LocationPickerProps = {
  value: Location;
  onChange: (location: Location) => void;
  autoLocateOnMount?: boolean;
};

type LocationTranslations = ReturnType<typeof useTranslation>["t"]["location"];

function normalizeCoordinate(value: number): number {
  return Number(value.toFixed(6));
}

function getBrowserLocationError(
  error: GeolocationPositionError,
  locationT: LocationTranslations,
): string {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return locationT.permissionDenied;
    case error.POSITION_UNAVAILABLE:
      return locationT.positionUnavailable;
    case error.TIMEOUT:
      return locationT.timeout;
    default:
      return locationT.unknownError;
  }
}

export function LocationPicker({
  value,
  onChange,
  autoLocateOnMount = false,
}: LocationPickerProps) {
  const { t } = useTranslation();
  const hasTriedAutoLocate = useRef(false);
  const [isLocating, setIsLocating] = useState(false);
  const [helperText, setHelperText] = useState<string>(
    autoLocateOnMount
      ? t.location.helperAuto
      : t.location.helperDefault,
  );
  const [error, setError] = useState<string>("");

  function setNextLocation(nextLocation: Location, message?: string) {
    onChange({
      latitude: normalizeCoordinate(nextLocation.latitude),
      longitude: normalizeCoordinate(nextLocation.longitude),
    });
    setError("");
    setHelperText(
      message ?? t.location.helperUpdated,
    );
  }

  function requestCurrentLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setError(t.location.noBrowserSupport);
      setHelperText(t.location.helperPickMap);
      return;
    }

    setIsLocating(true);
    setError("");
    setHelperText(t.location.helperRequesting);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setIsLocating(false);
        setNextLocation(
          {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
          t.location.helperCurrent,
        );
      },
      (positionError) => {
        setIsLocating(false);
        setError(getBrowserLocationError(positionError, t.location));
        setHelperText(t.location.helperClickToKeepMoving);
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
  }, [autoLocateOnMount, t]);

  return (
    <section className="location-section">
      <div className="location-toolbar">
        <div className="location-copy">
          <h3>{t.location.title}</h3>
          <p>{t.location.subtitle}</p>
        </div>
        <button
          className="button button-secondary"
          disabled={isLocating}
          onClick={requestCurrentLocation}
          type="button"
        >
          {isLocating ? t.location.locating : t.location.useCurrent}
        </button>
      </div>

      <LeafletLocationMap location={value} onChange={setNextLocation} />

      <p className="location-status">
        {t.location.status}
      </p>

      {error ? <p className="error-text">{error}</p> : null}
      {!error ? <p className="location-helper-text">{helperText}</p> : null}
    </section>
  );
}
