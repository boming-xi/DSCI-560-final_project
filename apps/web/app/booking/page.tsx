"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";

import { getFlowState, patchFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";

export default function BookingPage() {
  const { isCheckingAuth, session } = useProtectedRoute();
  const flow = getFlowState();
  const doctor = flow.selectedDoctor ?? flow.searchResult?.doctors[0] ?? null;
  const officialBookingUrl = doctor?.official_booking_url ?? null;
  const officialProfileUrl = doctor?.official_profile_url ?? null;

  useEffect(() => {
    if (!doctor) {
      return;
    }

    patchFlowState({ selectedDoctor: doctor });
  }, [doctor]);

  useEffect(() => {
    if (!officialBookingUrl) {
      return;
    }

    const redirectHandle = window.setTimeout(() => {
      window.location.assign(officialBookingUrl);
    }, 1200);

    return () => window.clearTimeout(redirectHandle);
  }, [officialBookingUrl]);

  const handoffSummary = useMemo(() => {
    if (!doctor) {
      return null;
    }

    return [
      doctor.provider_system ? `${doctor.provider_system} booking handoff` : "Third-party booking handoff",
      doctor.insurance_verification?.label ?? "Coverage should be rechecked on the provider site",
      doctor.booking_system_name ?? "Official scheduling page",
    ];
  }, [doctor]);

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Preparing your booking handoff...</div>
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
        <h1>Third-party booking handoff</h1>
        <p>
          This project does not complete appointments inside the site. We recommend the doctor,
          then hand you off to the provider&apos;s official booking page.
        </p>
      </section>

      {doctor ? (
        <section className="panel booking-layout booking-handoff-layout">
          <div>
            <span className="eyebrow">{doctor.specialty}</span>
            <h2>{doctor.name}</h2>
            <p>{doctor.clinic.name}</p>
            <p>{doctor.clinic.address}</p>
            <div className="badge-row">
              <span className="badge">{doctor.distance_km} km away</span>
              <span className="badge">{doctor.next_opening_label}</span>
              {doctor.provider_system ? <span className="badge">{doctor.provider_system}</span> : null}
              {doctor.pilot_region ? <span className="badge">{doctor.pilot_region}</span> : null}
            </div>
            <div className="info-box booking-handoff-box">
              <strong>What happens on this page</strong>
              <ul className="detail-list">
                <li>We preserve the recommended doctor and insurance context.</li>
                <li>You finish appointment booking on the provider&apos;s own website.</li>
                <li>This project does not create a confirmation number or hold a time slot.</li>
              </ul>
            </div>
          </div>

          <div className="booking-side-card booking-handoff-card">
            <h3>
              {officialBookingUrl
                ? "Redirecting to official booking"
                : "Official booking link unavailable"}
            </h3>
            <p className="subtle-copy">
              {officialBookingUrl
                ? `We are sending you to ${doctor.provider_system ?? "the provider"} to finish scheduling. If the redirect does not happen, use the button below.`
                : "This clinician does not currently have a live public scheduling link attached to the recommendation flow."}
            </p>

            {handoffSummary ? (
              <div className="badge-row compact-badge-row">
                {handoffSummary.map((item) => (
                  <span className="badge" key={item}>
                    {item}
                  </span>
                ))}
              </div>
            ) : null}

            <div className="form-actions">
              {officialBookingUrl ? (
                <a
                  className="button button-primary"
                  href={officialBookingUrl}
                >
                  {doctor.official_booking_label ?? "Open official booking"}
                </a>
              ) : null}

              {officialProfileUrl ? (
                <a
                  className="button button-secondary"
                  href={officialProfileUrl}
                >
                  View official provider profile
                </a>
              ) : null}

              <Link className="button button-secondary" href="/doctors">
                Back to doctors
              </Link>
            </div>

            {!officialBookingUrl ? (
              <div className="notice-box">
                Official booking handoff is currently available for clinicians connected to the
                live LA provider pilot, including UCLA Health.
              </div>
            ) : null}
          </div>
        </section>
      ) : (
        <section className="panel error-panel">
          Return to recommendations and choose a doctor before opening booking handoff.
        </section>
      )}
    </main>
  );
}
