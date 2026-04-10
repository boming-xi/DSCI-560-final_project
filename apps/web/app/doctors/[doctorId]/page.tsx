"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { RankingExplanation } from "@/components/RankingExplanation";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import type { DoctorProfile } from "@/lib/types";

function formatAvailabilityLabel(doctor: DoctorProfile) {
  return doctor.availability_days === 0
    ? "Same-day availability"
    : `Next opening ${doctor.next_opening_label.toLowerCase()}`;
}

function findCachedDoctor(doctorId: string): DoctorProfile | null {
  const flow = getFlowState();
  return (
    flow.selectedDoctor?.id === doctorId
      ? flow.selectedDoctor
      : flow.searchResult?.doctors.find((doctor) => doctor.id === doctorId)
  ) ?? null;
}

export default function DoctorDetailPage() {
  const params = useParams<{ doctorId: string }>();
  const router = useRouter();
  const { isCheckingAuth, session } = useProtectedRoute();
  const doctorId = Array.isArray(params.doctorId) ? params.doctorId[0] : params.doctorId;
  const cachedDoctor = useMemo(() => (doctorId ? findCachedDoctor(doctorId) : null), [doctorId]);
  const [doctor, setDoctor] = useState<DoctorProfile | null>(cachedDoctor);
  const [isLoading, setIsLoading] = useState(!cachedDoctor);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDoctor() {
      if (!doctorId || isCheckingAuth || !session) {
        return;
      }

      if (cachedDoctor) {
        setDoctor(cachedDoctor);
        patchFlowState({ selectedDoctor: cachedDoctor });
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");
      try {
        const profile = await api.getDoctor(doctorId);
        setDoctor(profile);
        patchFlowState({ selectedDoctor: profile });
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load this doctor profile.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDoctor();
  }, [cachedDoctor, doctorId, isCheckingAuth, session]);

  function handleBook() {
    if (!doctor) {
      return;
    }
    patchFlowState({ selectedDoctor: doctor });
    router.push("/booking");
  }

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Checking your account before opening doctor details...</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="page-shell">
      <section className="panel doctor-detail-hero">
        <div className="doctor-detail-header">
          <div>
            <span className="eyebrow">Doctor profile</span>
            <h1>{doctor?.name ?? "Doctor details"}</h1>
            <p>
              {doctor
                ? `${doctor.specialty} at ${doctor.clinic.name}`
                : "Loading clinician details and recommendation context."}
            </p>
          </div>
          <div className="doctor-detail-actions">
            <Link className="button button-secondary" href="/doctors">
              Back to recommendations
            </Link>
            <button
              className="button button-primary"
              disabled={!doctor}
              onClick={handleBook}
              type="button"
            >
              Book this doctor
            </button>
          </div>
        </div>

        {doctor ? (
          <>
            <div className="badge-row">
              <span className="badge">{doctor.specialty}</span>
              <span className="badge">{doctor.years_experience} yrs experience</span>
              <span className="badge">{doctor.rating} rating</span>
              <span className="badge">{doctor.review_count} reviews</span>
              <span className="badge">{formatAvailabilityLabel(doctor)}</span>
              <span className="badge">{doctor.distance_km} km away</span>
            </div>
            <p className="doctor-detail-intro">{doctor.profile_blurb}</p>
          </>
        ) : null}
      </section>

      {isLoading ? <div className="panel">Loading full doctor profile...</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      {doctor ? (
        <>
          <section className="summary-grid">
            <article className="panel summary-card">
              <span className="eyebrow">Profile</span>
              <h2>{doctor.accepts_new_patients ? "Accepting new patients" : "Limited new-patient access"}</h2>
              <p>{doctor.care_approach}</p>
            </article>
            <article className="panel summary-card">
              <span className="eyebrow">Access</span>
              <h2>{doctor.next_opening_label}</h2>
              <p>
                {doctor.appointment_modes.join(", ")} with{" "}
                {doctor.clinic.open_weekends ? "weekend clinic support" : "weekday clinic scheduling"}.
              </p>
            </article>
          </section>

          <RankingExplanation doctor={doctor} />

          <section className="doctor-detail-grid">
            <article className="panel doctor-detail-card">
              <span className="eyebrow">Common visits</span>
              <h3>What this doctor commonly helps with</h3>
              <ul className="detail-list">
                {doctor.clinical_focus.map((focus) => (
                  <li key={focus}>{focus}</li>
                ))}
              </ul>
            </article>

            <article className="panel doctor-detail-card">
              <span className="eyebrow">Visit style</span>
              <h3>What patients usually notice</h3>
              <ul className="detail-list">
                {doctor.visit_highlights.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>

            <article className="panel doctor-detail-card">
              <span className="eyebrow">Credentials</span>
              <h3>Training and certification</h3>
              <h4>Education</h4>
              <ul className="detail-list">
                {doctor.education.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <h4>Board certifications</h4>
              <ul className="detail-list">
                {doctor.board_certifications.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>

            <article className="panel doctor-detail-card">
              <span className="eyebrow">Clinic access</span>
              <h3>{doctor.clinic.name}</h3>
              <div className="doctor-detail-meta-list">
                <p>{doctor.clinic.address}</p>
                <p>{doctor.clinic.city}, {doctor.clinic.state} {doctor.clinic.zip}</p>
                <p>{doctor.clinic.phone}</p>
                <p>Clinic languages: {doctor.clinic.languages.join(", ")}</p>
                <p>Care types: {doctor.clinic.care_types.join(", ")}</p>
              </div>
              <div className="badge-row compact-badge-row">
                <span className="badge">
                  {doctor.telehealth ? "Telehealth available" : "In-person only"}
                </span>
                <span className="badge">
                  {doctor.clinic.open_weekends ? "Open weekends" : "Weekday clinic"}
                </span>
                <span className="badge">
                  {doctor.clinic.urgent_care ? "Urgent care on site" : "Standard clinic scheduling"}
                </span>
              </div>
            </article>

            <article className="panel doctor-detail-card doctor-detail-card-wide">
              <span className="eyebrow">Insurance and booking</span>
              <h3>Coverage, referrals, and appointment setup</h3>
              <div className="doctor-detail-insurance-grid">
                <div>
                  <h4>Accepted plans</h4>
                  <ul className="detail-list">
                    {doctor.accepted_insurance.map((plan) => (
                      <li key={plan}>{plan}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>Visit setup</h4>
                  <ul className="detail-list">
                    <li>{doctor.accepts_new_patients ? "Accepting new patients" : "May require a referral or waitlist"}</li>
                    <li>{doctor.next_opening_label} next opening</li>
                    <li>{doctor.estimated_cost ? `$${doctor.estimated_cost} estimated copay` : "Estimated cost depends on plan"}</li>
                    <li>{doctor.referral_required ? "Specialist referral may be required" : "Referral usually not required"}</li>
                  </ul>
                </div>
              </div>
              <div className="form-actions">
                <button className="button button-primary" onClick={handleBook} type="button">
                  Continue to booking
                </button>
                <Link className="button button-secondary" href="/chat">
                  Ask assistant about this doctor
                </Link>
              </div>
            </article>
          </section>
        </>
      ) : null}
    </main>
  );
}
