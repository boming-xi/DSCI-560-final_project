"use client";

import { useMemo, useState } from "react";

import type { DoctorProfile, InsuranceSummary, TriageRecommendation } from "@/lib/types";

type CarePassportCardProps = {
  symptomText?: string;
  triage?: TriageRecommendation;
  insuranceSummary?: InsuranceSummary;
  doctor?: DoctorProfile | null;
  insuranceQuery?: string;
  bookingUrl?: string | null;
};

function buildPassportText({
  symptomText,
  triage,
  insuranceSummary,
  doctor,
  insuranceQuery,
  bookingUrl,
}: CarePassportCardProps): string {
  const insuranceLine = insuranceSummary?.matched
    ? `${insuranceSummary.provider} ${insuranceSummary.plan_name}`
    : insuranceQuery?.trim()
    ? `Insurance entered for review: ${insuranceQuery.trim()}`
    : "No insurance plan attached";

  const doctorLine = doctor
    ? `${doctor.name}, ${doctor.specialty}, ${doctor.clinic.name}`
    : "Doctor not selected";

  return [
    "AI Healthcare Assistant - Personal Care Passport",
    "",
    `Symptoms: ${symptomText?.trim() || "Not provided"}`,
    `Recommended care path: ${triage?.care_type || "Not available yet"}`,
    `Urgency band: ${triage?.urgency_level || "Not available yet"}`,
    `Insurance status: ${insuranceLine}`,
    `Recommended doctor: ${doctorLine}`,
    `Network check: ${doctor?.insurance_verification?.label || "Pending"}`,
    `Official booking link: ${bookingUrl || doctor?.official_booking_url || "Not attached"}`,
  ].join("\n");
}

export function CarePassportCard(props: CarePassportCardProps) {
  const [feedback, setFeedback] = useState("");

  const passportText = useMemo(() => buildPassportText(props), [props]);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(passportText);
      setFeedback("Care passport copied.");
    } catch {
      setFeedback("Copy is not available in this browser.");
    }
  }

  async function handleShare() {
    if (!navigator.share) {
      await handleCopy();
      return;
    }

    try {
      await navigator.share({
        title: "Personal care passport",
        text: passportText,
        url: props.bookingUrl || props.doctor?.official_booking_url || undefined,
      });
      setFeedback("Care passport shared.");
    } catch {
      setFeedback("");
    }
  }

  return (
    <section className="panel care-passport-card">
      <div className="care-passport-header">
        <div>
          <span className="eyebrow">Personal care passport</span>
          <h2>Your shareable care summary</h2>
          <p>
            This summary captures the current symptom context, care path,
            insurance status, recommended doctor, and official booking handoff.
          </p>
        </div>
        <div className="form-actions">
          <button className="button button-secondary" onClick={handleCopy} type="button">
            Copy summary
          </button>
          <button className="button button-primary" onClick={handleShare} type="button">
            Share summary
          </button>
        </div>
      </div>

      <div className="care-passport-grid">
        <article className="care-passport-item">
          <span className="eyebrow">Symptoms</span>
          <h3>{props.triage?.summary ?? "Symptom review pending"}</h3>
          <p>{props.symptomText ?? "Add symptoms to generate a full passport."}</p>
        </article>

        <article className="care-passport-item">
          <span className="eyebrow">Care path</span>
          <h3>{props.triage?.care_type ?? "Not selected yet"}</h3>
          <p>{props.triage?.next_step ?? "The care path will appear after symptom triage."}</p>
        </article>

        <article className="care-passport-item">
          <span className="eyebrow">Insurance status</span>
          <h3>
            {props.insuranceSummary?.matched
              ? `${props.insuranceSummary.provider} ${props.insuranceSummary.plan_name}`
              : props.insuranceQuery?.trim() || "No plan attached"}
          </h3>
          <p>
            {props.insuranceSummary?.notes?.[0] ??
              "Insurance guidance will appear here once a plan is uploaded or selected."}
          </p>
        </article>

        <article className="care-passport-item">
          <span className="eyebrow">Recommended doctor</span>
          <h3>{props.doctor?.name ?? "Doctor not chosen yet"}</h3>
          <p>
            {props.doctor
              ? `${props.doctor.specialty} at ${props.doctor.clinic.name}`
              : "Choose a doctor to complete this passport."}
          </p>
        </article>
      </div>

      {feedback ? <p className="muted-copy">{feedback}</p> : null}
    </section>
  );
}
