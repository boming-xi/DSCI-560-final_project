"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { BookingModal } from "@/components/BookingModal";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import type { BookingConfirmation, DoctorProfile, TimeSlot } from "@/lib/types";

export default function BookingPage() {
  const { isCheckingAuth, session } = useProtectedRoute();
  const [doctor, setDoctor] = useState<DoctorProfile | null>(null);
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [slotSource, setSlotSource] = useState<"external_sync" | "demo_fallback" | string>(
    "demo_fallback"
  );
  const [confirmation, setConfirmation] = useState<BookingConfirmation | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadBookingContext() {
      if (isCheckingAuth || !session) {
        return;
      }
      const flow = getFlowState();
      const selectedDoctor = flow.selectedDoctor ?? flow.searchResult?.doctors[0] ?? null;
      if (!selectedDoctor) {
        setError("Choose a doctor from the recommendation page first.");
        setIsLoading(false);
        return;
      }

      try {
        const slotsResponse = await api.getBookingSlots(selectedDoctor.id);
        setDoctor(selectedDoctor);
        setSlots(slotsResponse.slots);
        setSlotSource(slotsResponse.source);
        setConfirmation(flow.booking ?? null);
        patchFlowState({ selectedDoctor });
      } catch (loadError) {
        setError(
          loadError instanceof Error ? loadError.message : "Unable to load booking slots."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadBookingContext();
  }, [isCheckingAuth, session]);

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Checking your account before opening booking...</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="page-shell">
      <section className="results-header panel">
        <span className="eyebrow">Step 4</span>
        <h1>Booking support</h1>
        <p>Review appointment context and confirm the next available slot.</p>
      </section>

      {isLoading ? <div className="panel">Loading booking options...</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      {doctor ? (
        <section className="panel booking-layout">
          <div>
            <span className="eyebrow">{doctor.specialty}</span>
            <h2>{doctor.name}</h2>
            <p>{doctor.clinic.name}</p>
            <p>{doctor.clinic.address}</p>
            <div className="badge-row">
              <span className="badge">{doctor.distance_km} km away</span>
              <span className="badge">
                {doctor.telehealth ? "Telehealth available" : "In-person only"}
              </span>
              <span className="badge">{doctor.languages.join(", ")}</span>
            </div>
          </div>

          <div className="booking-side-card">
            <h3>Available slots</h3>
            <p className="subtle-copy">
              {slotSource === "external_sync"
                ? "Using synced scheduling data from the external slot feed."
                : "Using demo fallback availability."}
            </p>
            <ul className="slot-list">
              {slots.map((slot) => (
                <li key={slot.start}>
                  {slot.label}
                  {slot.appointment_mode ? ` · ${slot.appointment_mode}` : ""}
                </li>
              ))}
            </ul>
            <div className="form-actions">
              <button
                className="button button-primary"
                onClick={() => setIsModalOpen(true)}
                type="button"
              >
                Open booking form
              </button>
              <Link className="button button-secondary" href="/doctors">
                Back to doctors
              </Link>
            </div>
          </div>
        </section>
      ) : null}

      {confirmation ? (
        <section className="panel confirmation-card">
          <span className="eyebrow">Confirmation</span>
          <h2>{confirmation.confirmation_id}</h2>
          <p>
            Appointment requested with {confirmation.doctor_name} at{" "}
            {confirmation.clinic_name}.
          </p>
          <p>{new Date(confirmation.slot).toLocaleString()}</p>
          <ul className="detail-list">
            {confirmation.next_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {doctor ? (
        <BookingModal
          doctor={doctor}
          slots={slots}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onBooked={(nextConfirmation) => setConfirmation(nextConfirmation)}
        />
      ) : null}
    </main>
  );
}
