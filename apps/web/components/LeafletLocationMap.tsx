"use client";

import { useEffect, useMemo } from "react";
import L from "leaflet";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

import type { Location } from "@/lib/types";

type LeafletLocationMapProps = {
  location: Location;
  onChange: (location: Location) => void;
};

const locationPin = L.divIcon({
  className: "location-pin",
  html: "<span></span>",
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

function normalizeCoordinate(value: number): number {
  return Number(value.toFixed(6));
}

function RecenterMap({ location }: { location: Location }) {
  const map = useMap();

  useEffect(() => {
    map.flyTo([location.latitude, location.longitude], Math.max(map.getZoom(), 13), {
      animate: true,
      duration: 0.6,
    });
  }, [location.latitude, location.longitude, map]);

  return null;
}

function MapClickHandler({ onChange }: { onChange: (location: Location) => void }) {
  useMapEvents({
    click(event) {
      onChange({
        latitude: normalizeCoordinate(event.latlng.lat),
        longitude: normalizeCoordinate(event.latlng.lng),
      });
    },
  });

  return null;
}

export function LeafletLocationMap({
  location,
  onChange,
}: LeafletLocationMapProps) {
  const center = useMemo(
    () => [location.latitude, location.longitude] as [number, number],
    [location.latitude, location.longitude],
  );

  return (
    <div className="location-map-shell">
      <MapContainer
        center={center}
        className="location-map"
        scrollWheelZoom
        zoom={13}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClickHandler onChange={onChange} />
        <RecenterMap location={location} />
        <Marker
          draggable
          eventHandlers={{
            dragend(event) {
              const nextPosition = (event.target as L.Marker).getLatLng();
              onChange({
                latitude: normalizeCoordinate(nextPosition.lat),
                longitude: normalizeCoordinate(nextPosition.lng),
              });
            },
          }}
          icon={locationPin}
          position={center}
        />
      </MapContainer>
    </div>
  );
}
