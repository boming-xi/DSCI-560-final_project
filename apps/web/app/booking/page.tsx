"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";

import { CarePassportCard } from "@/components/CarePassportCard";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import { useProtectedRoute } from "@/lib/useProtectedRoute";

export default function BookingPage() {
  const { t } = useTranslation();
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

  const handoffSummary = useMemo(() => {
    if (!doctor) {
      return null;
    }

    return [
      doctor.provider_system
        ? `${doctor.provider_system} ${t.booking.thirdPartyHandoff.toLowerCase()}`
        : t.booking.thirdPartyHandoff,
      doctor.insurance_verification?.label ?? t.booking.coverageRecheck,
      doctor.booking_system_name ?? t.booking.officialSchedulingPage,
    ];
  }, [doctor, t]);

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">{t.booking.preparing}</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="page-shell">
      <section className="results-header panel">
        <span className="eyebrow">{t.booking.step}</span>
        <h1>{t.booking.title}</h1>
        <p>{t.booking.subtitle}</p>
      </section>

      {doctor ? (
        <>
          <section className="panel booking-layout booking-handoff-layout">
            <div>
              <span className="eyebrow">{doctor.specialty}</span>
              <h2>{doctor.name}</h2>
              <p>{doctor.clinic.name}</p>
              <p>{doctor.clinic.address}</p>
              <div className="badge-row">
                <span className="badge">
                  {t.booking.distanceAway.replace("{distance}", String(doctor.distance_km))}
                </span>
                <span className="badge">{doctor.next_opening_label}</span>
                {doctor.provider_system ? <span className="badge">{doctor.provider_system}</span> : null}
                {doctor.pilot_region ? <span className="badge">{doctor.pilot_region}</span> : null}
              </div>
              <div className="booking-step-grid">
                <article className="booking-step-card">
                  <span className="eyebrow">{t.booking.step}</span>
                  <strong>{t.booking.handoffPoint1}</strong>
                </article>
                <article className="booking-step-card">
                  <span className="eyebrow">{t.booking.whatHappens}</span>
                  <strong>{t.booking.handoffPoint2}</strong>
                </article>
                <article className="booking-step-card">
                  <span className="eyebrow">{t.booking.thirdPartyHandoff}</span>
                  <strong>{t.booking.handoffPoint3}</strong>
                </article>
              </div>
              <div className="info-box booking-handoff-box">
                <strong>{t.booking.whatHappens}</strong>
                <p className="subtle-copy">
                  {officialBookingUrl
                    ? t.booking.officialBookingReadyBody.replace(
                        "{provider}",
                        doctor.provider_system ?? t.booking.providerFallback,
                      )
                    : t.booking.officialBookingUnavailableBody}
                </p>
              </div>
            </div>

            <div className="booking-side-card booking-handoff-card">
              <h3>
                {officialBookingUrl
                  ? t.booking.officialBookingReady
                  : t.booking.officialBookingUnavailable}
              </h3>
              <p className="subtle-copy">
                {officialBookingUrl
                  ? t.booking.officialBookingReadyBody.replace(
                      "{provider}",
                      doctor.provider_system ?? t.booking.providerFallback,
                    )
                  : t.booking.officialBookingUnavailableBody}
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
                    {doctor.official_booking_label ?? t.booking.openOfficialBooking}
                  </a>
                ) : null}

                {officialProfileUrl ? (
                  <a
                    className="button button-secondary"
                    href={officialProfileUrl}
                  >
                    {t.booking.viewOfficialProviderProfile}
                  </a>
                ) : null}

                <Link className="button button-secondary" href="/doctors">
                  {t.booking.backToDoctors}
                </Link>
              </div>

              {!officialBookingUrl ? (
                <div className="notice-box">
                  {t.booking.pilotNotice}
                </div>
              ) : null}
            </div>
          </section>

          <CarePassportCard
            bookingUrl={officialBookingUrl}
            doctor={doctor}
            insuranceQuery={flow.insuranceQuery}
            insuranceSummary={flow.insuranceSummary}
            symptomText={flow.symptomText}
            triage={flow.triage}
          />
        </>
      ) : (
        <section className="panel error-panel">
          {t.booking.chooseDoctorFirst}
        </section>
      )}
    </main>
  );
}
