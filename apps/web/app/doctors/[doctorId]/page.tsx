"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { RankingExplanation } from "@/components/RankingExplanation";
import { api } from "@/lib/api";
import { beginDoctorBooking } from "@/lib/doctor-booking";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import type { DoctorProfile } from "@/lib/types";

function formatAvailabilityLabel(
  doctor: DoctorProfile,
  t: ReturnType<typeof useTranslation>["t"],
) {
  return doctor.availability_days === 0
    ? t.doctorCard.sameDayAvailability
    : t.doctorDetail.nextOpening.replace("{label}", doctor.next_opening_label.toLowerCase());
}

function findCachedDoctor(doctorId: string): DoctorProfile | null {
  const flow = getFlowState();
  return (
    flow.selectedDoctor?.id === doctorId
      ? flow.selectedDoctor
      : flow.searchResult?.doctors.find((doctor) => doctor.id === doctorId)
  ) ?? null;
}

function hasPublicRating(doctor: DoctorProfile) {
  return doctor.rating > 0 && doctor.review_count > 0;
}

export default function DoctorDetailPage() {
  const { t } = useTranslation();
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
            : t.doctorDetail.loadError,
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDoctor();
  }, [cachedDoctor, doctorId, isCheckingAuth, session, t]);

  function handleBook() {
    if (!doctor) {
      return;
    }
    beginDoctorBooking(doctor, {
      onInternalBooking: () => router.push("/booking"),
    });
  }

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">{t.doctorDetail.loadingDetails}</div>
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
            <span className="eyebrow">{t.doctorDetail.doctorProfile}</span>
            <h1>{doctor?.name ?? t.doctorDetail.doctorDetails}</h1>
            <p>
              {doctor
                ? `${doctor.specialty} at ${doctor.clinic.name}`
                : t.doctorDetail.gatheringDetails}
            </p>
          </div>
          <div className="doctor-detail-actions">
            <Link className="button button-secondary" href="/doctors">
              {t.doctorDetail.backToRecommendations}
            </Link>
            <button
              className="button button-primary"
              disabled={!doctor}
              onClick={handleBook}
              type="button"
            >
              {doctor?.official_booking_label ?? t.doctorCard.bookDoctor}
            </button>
          </div>
        </div>

        {doctor ? (
          <>
            <div className="badge-row">
              <span className="badge">{doctor.specialty}</span>
              <span className="badge">{doctor.years_experience} yrs experience</span>
              {hasPublicRating(doctor) ? (
                <>
                  <span className="badge">{doctor.rating} {t.doctorDetail.rating}</span>
                  <span className="badge">{doctor.review_count} {t.doctorDetail.reviews}</span>
                </>
              ) : (
                <span className="badge">{t.doctorDetail.publicRatingNotListed}</span>
              )}
              <span className="badge">{formatAvailabilityLabel(doctor, t)}</span>
              <span className="badge">
                {t.booking.distanceAway.replace("{distance}", String(doctor.distance_km))}
              </span>
              {doctor.provider_system ? <span className="badge">{doctor.provider_system}</span> : null}
              {doctor.pilot_region ? <span className="badge">{doctor.pilot_region}</span> : null}
            </div>
            <p className="doctor-detail-intro">{doctor.profile_blurb}</p>
          </>
        ) : null}
      </section>

      {isLoading ? <div className="panel">{t.doctorDetail.loadingProfile}</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      {doctor ? (
        <>
          <section className="summary-grid">
            <article className="panel summary-card">
              <span className="eyebrow">{t.doctorDetail.profile}</span>
              <h2>
                {doctor.accepts_new_patients
                  ? t.doctorDetail.acceptingNewPatients
                  : t.doctorDetail.limitedNewPatientAccess}
              </h2>
              <p>{doctor.care_approach}</p>
            </article>
            <article className="panel summary-card">
              <span className="eyebrow">{t.doctorDetail.access}</span>
              <h2>{doctor.official_booking_url ? t.doctorDetail.officialBookingAvailable : doctor.next_opening_label}</h2>
              <p>
                {doctor.official_booking_url
                  ? t.doctorDetail.officialSchedulingLine.replace(
                      "{provider}",
                      doctor.provider_system ?? t.booking.providerFallback,
                    )
                  : t.doctorDetail.clinicScheduleLine
                      .replace("{modes}", doctor.appointment_modes.join(", "))
                      .replace(
                        "{schedule}",
                        doctor.clinic.open_weekends
                          ? t.doctorDetail.weekendSupport
                          : t.doctorDetail.weekdayScheduling,
                      )}
              </p>
            </article>
          </section>

          <RankingExplanation doctor={doctor} />

          <section className="doctor-detail-grid">
            <article className="panel doctor-detail-card">
              <span className="eyebrow">{t.doctorDetail.commonVisits}</span>
              <h3>{t.doctorDetail.commonlyHelps}</h3>
              <ul className="detail-list">
                {doctor.clinical_focus.map((focus) => (
                  <li key={focus}>{focus}</li>
                ))}
              </ul>
            </article>

            <article className="panel doctor-detail-card">
              <span className="eyebrow">{t.doctorDetail.visitStyle}</span>
              <h3>{t.doctorDetail.whatPatientsNotice}</h3>
              <ul className="detail-list">
                {doctor.visit_highlights.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>

            <article className="panel doctor-detail-card">
              <span className="eyebrow">{t.doctorDetail.credentials}</span>
              <h3>{t.doctorDetail.trainingCertification}</h3>
              <h4>{t.doctorDetail.education}</h4>
              <ul className="detail-list">
                {doctor.education.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <h4>{t.doctorDetail.boardCertifications}</h4>
              <ul className="detail-list">
                {doctor.board_certifications.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>

            <article className="panel doctor-detail-card">
              <span className="eyebrow">{t.doctorDetail.clinicAccess}</span>
              <h3>{doctor.clinic.name}</h3>
              <div className="doctor-detail-meta-list">
                <p>{doctor.clinic.address}</p>
                <p>{doctor.clinic.city}, {doctor.clinic.state} {doctor.clinic.zip}</p>
                <p>{doctor.clinic.phone}</p>
                <p>{t.doctorDetail.clinicLanguages}: {doctor.clinic.languages.join(", ")}</p>
                <p>{t.doctorDetail.careTypes}: {doctor.clinic.care_types.join(", ")}</p>
              </div>
              <div className="badge-row compact-badge-row">
                <span className="badge">
                  {doctor.telehealth ? t.doctorDetail.telehealthAvailable : t.doctorDetail.inPersonOnly}
                </span>
                <span className="badge">
                  {doctor.clinic.open_weekends ? t.doctorDetail.openWeekends : t.doctorDetail.weekdayClinic}
                </span>
                <span className="badge">
                  {doctor.clinic.urgent_care ? t.doctorDetail.urgentCareOnSite : t.doctorDetail.standardScheduling}
                </span>
              </div>
            </article>

            <article className="panel doctor-detail-card doctor-detail-card-wide">
              <span className="eyebrow">{t.doctorDetail.insuranceBooking}</span>
              <h3>{t.doctorDetail.coverageReferralsSetup}</h3>
              <div className="doctor-detail-insurance-grid">
                <div>
                  <h4>{t.doctorDetail.acceptedPlans}</h4>
                  <ul className="detail-list">
                    {doctor.accepted_insurance.map((plan) => (
                      <li key={plan}>{plan}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>{t.doctorCard.networkVerification}</h4>
                  {doctor.insurance_verification ? (
                    <>
                      <p>{doctor.insurance_verification.label}</p>
                      <p>{doctor.insurance_verification.reason}</p>
                      {doctor.insurance_verification.evidence.length ? (
                        <ul className="detail-list">
                          {doctor.insurance_verification.evidence.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : null}
                      {doctor.insurance_verification.network_url ? (
                        <p>
                          <a
                            href={doctor.insurance_verification.network_url}
                            rel="noreferrer"
                            target="_blank"
                          >
                            {t.doctors.openOfficialNetworkDirectory}
                          </a>
                        </p>
                      ) : null}
                    </>
                  ) : (
                    <p>{t.doctorDetail.selectPlanFirst}</p>
                  )}
                </div>
                <div>
                  <h4>{t.doctorDetail.visitSetup}</h4>
                  <ul className="detail-list">
                    <li>{doctor.accepts_new_patients ? t.doctorDetail.acceptingNewPatients : t.doctorDetail.mayRequireReferral}</li>
                    <li>{t.doctorDetail.nextOpening.replace("{label}", doctor.next_opening_label)}</li>
                    <li>
                      {doctor.estimated_cost
                        ? t.doctorCard.copayEstimate.replace("{amount}", `$${doctor.estimated_cost}`)
                        : t.doctorDetail.estimatedCostDepends}
                    </li>
                    <li>{doctor.referral_required ? t.doctorDetail.specialistReferralMayBeRequired : t.doctorDetail.referralUsuallyNotRequired}</li>
                    {doctor.booking_system_name ? <li>{doctor.booking_system_name}</li> : null}
                    {doctor.booking_note ? <li>{doctor.booking_note}</li> : null}
                  </ul>
                </div>
              </div>
              {doctor.official_profile_url || doctor.official_booking_url ? (
                <div className="info-box">
                  <strong>
                    {t.doctorDetail.providerBookingPath.replace(
                      "{provider}",
                      doctor.provider_system ?? t.doctorCard.officialBooking,
                    )}
                  </strong>
                  <p>
                    {doctor.official_booking_url
                      ? t.doctorDetail.livePublicPageBooking
                      : t.doctorDetail.publicProfileOnly}
                  </p>
                  <div className="form-actions">
                    {doctor.official_booking_url ? (
                      <a
                        className="button button-primary"
                        href={doctor.official_booking_url}
                      >
                        {doctor.official_booking_label ?? t.doctorDetail.openOfficialBooking}
                      </a>
                    ) : null}
                    {doctor.official_profile_url ? (
                      <a
                        className="button button-secondary"
                        href={doctor.official_profile_url}
                      >
                        {t.doctorCard.viewOfficialProfile}
                      </a>
                    ) : null}
                  </div>
                </div>
              ) : null}
              <div className="form-actions">
                <button className="button button-primary" onClick={handleBook} type="button">
                  {doctor.official_booking_label ?? t.doctorDetail.continueToBooking}
                </button>
              </div>
            </article>
          </section>
        </>
      ) : null}
    </main>
  );
}
