"use client";

import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import type {
  BookingConfirmation,
  DoctorProfile,
  TimeSlot,
} from "@/lib/types";

type BookingModalProps = {
  doctor: DoctorProfile;
  slots: TimeSlot[];
  isOpen: boolean;
  onClose: () => void;
  onBooked: (confirmation: BookingConfirmation) => void;
};

export function BookingModal({
  doctor,
  slots,
  isOpen,
  onClose,
  onBooked,
}: BookingModalProps) {
  const flow = getFlowState();
  const [patientName, setPatientName] = useState("Boming Xi");
  const [email, setEmail] = useState("boming@example.com");
  const [preferredSlot, setPreferredSlot] = useState(slots[0]?.start ?? "");
  const [notes, setNotes] = useState(
    flow.symptomText ? `Reason for visit: ${flow.symptomText}` : ""
  );
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) {
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const confirmation = await api.createBooking({
        doctor_id: doctor.id,
        patient_name: patientName,
        email,
        preferred_slot: preferredSlot,
        insurance_plan_id: flow.insuranceSummary?.plan_id ?? undefined,
        symptom_text: flow.symptomText,
        notes,
      });

      patchFlowState({ booking: confirmation });
      onBooked(confirmation);
      onClose();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to book appointment."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal-card">
        <div className="panel-heading">
          <span className="eyebrow">Step 4</span>
          <h3>Book with {doctor.name}</h3>
          <p>{doctor.clinic.name}</p>
        </div>

        <form className="form-panel" onSubmit={handleSubmit}>
          <label className="field">
            <span>Patient name</span>
            <input value={patientName} onChange={(event) => setPatientName(event.target.value)} />
          </label>
          <label className="field">
            <span>Email</span>
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="field">
            <span>Preferred slot</span>
            <select
              value={preferredSlot}
              onChange={(event) => setPreferredSlot(event.target.value)}
            >
              {slots.map((slot) => (
                <option key={slot.start} value={slot.start}>
                  {slot.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Notes</span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={4}
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <div className="form-actions">
            <button className="button button-primary" disabled={isLoading} type="submit">
              {isLoading ? "Booking..." : "Confirm booking"}
            </button>
            <button className="button button-secondary" onClick={onClose} type="button">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

