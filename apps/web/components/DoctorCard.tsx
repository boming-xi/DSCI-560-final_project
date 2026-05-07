"use client";

import { useTranslation } from "@/lib/LanguageProvider";
import type { DoctorProfile } from "@/lib/types";

type DoctorCardProps = {
  doctor: DoctorProfile;
  highlighted?: boolean;
  rank?: number;
  onBook: () => void;
  onView: () => void;
};

export function DoctorCard({
  doctor,
  highlighted = false,
  rank,
  onBook,
  onView,
}: DoctorCardProps) {
  const { t } = useTranslation();
  const hasPublicRating = doctor.rating > 0 && doctor.review_count > 0;

  return (
    <article className={`panel doctor-card ${highlighted ? "recommended-card" : ""}`}>
      <div className="doctor-card-top">
        <div>
          <span className="eyebrow">{doctor.specialty}</span>
          {highlighted ? <span className="recommended-doctor-tag">{t.doctorCard.advisorPick}</span> : null}
          <h3>{doctor.name}</h3>
          <p>{doctor.profile_blurb}</p>
        </div>
        <div className="score-badge">
          <strong>{rank ? `#${rank}` : t.doctorCard.topBadge}</strong>
          <span>{t.doctorCard.shortlistRank}</span>
        </div>
      </div>

      <div className="badge-row">
        <span className="badge">
          {doctor.years_experience} {t.doctorCard.yearsExperience}
        </span>
        <span className="badge">
          {t.booking.distanceAway.replace("{distance}", String(doctor.distance_km))}
        </span>
        <span className="badge">
          {hasPublicRating ? `${doctor.rating} ${t.doctorDetail.rating}` : t.doctorCard.officialProviderProfile}
        </span>
        <span className="badge">{doctor.next_opening_label}</span>
        <span className="badge">
          {doctor.availability_days === 0
            ? t.doctorCard.sameDayAvailability
            : t.doctorCard.availableInDays.replace("{days}", String(doctor.availability_days))}
        </span>
        {doctor.provider_system ? <span className="badge">{doctor.provider_system}</span> : null}
        {doctor.pilot_region ? <span className="badge">{doctor.pilot_region}</span> : null}
      </div>

      {doctor.clinical_focus.length ? (
        <div className="doctor-focus-preview">
          <h4>{t.doctorCard.goodFitFor}</h4>
          <div className="badge-row compact-badge-row">
            {doctor.clinical_focus.slice(0, 3).map((focus) => (
              <span className="badge" key={focus}>
                {focus}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="doctor-meta-grid">
        <div>
          <h4>{t.doctorCard.clinic}</h4>
          <p>{doctor.clinic.name}</p>
          <p>{doctor.clinic.address}</p>
        </div>
        <div>
          <h4>{t.doctorCard.languages}</h4>
          <p>{doctor.languages.join(", ")}</p>
        </div>
        <div>
          <h4>{t.doctorCard.networkVerification}</h4>
          <p>{doctor.insurance_verification?.label ?? t.doctorCard.insurancePending}</p>
          <p className="subtle-copy">
            {doctor.insurance_verification?.reason ?? t.doctorCard.addPlanToCheck}
          </p>
        </div>
        <div>
          <h4>{t.doctorCard.estimatedCost}</h4>
          <p>
            {doctor.estimated_cost
              ? t.doctorCard.copayEstimate.replace("{amount}", `$${doctor.estimated_cost}`)
              : t.doctorCard.planNeeded}
          </p>
        </div>
      </div>

      {doctor.official_booking_url ? (
        <div className="info-box">
          <strong>{doctor.booking_system_name ?? doctor.provider_system ?? t.doctorCard.officialBooking}</strong>
          <p>
            {doctor.booking_note ?? t.doctorCard.officialBookingFallback}
          </p>
          <div className="form-actions">
            <a href={doctor.official_profile_url ?? doctor.official_booking_url}>
              {t.doctorCard.viewOfficialProfile}
            </a>
          </div>
        </div>
      ) : null}

      {doctor.insurance_verification?.network_url ? (
        <div className="info-box">
          <strong>{doctor.insurance_verification.label}</strong>
          <p>{doctor.insurance_verification.reason}</p>
          <a href={doctor.insurance_verification.network_url} rel="noreferrer" target="_blank">
            {t.doctors.openOfficialNetworkDirectory}
          </a>
        </div>
      ) : null}

      {doctor.referral_required ? (
        <div className="notice-box">
          {t.doctorCard.referralNotice}
        </div>
      ) : null}

      <div className="form-actions">
        <button className="button button-secondary" onClick={onView} type="button">
          {t.doctorCard.viewFullProfile}
        </button>
        <button className="button button-primary" onClick={onBook} type="button">
          {doctor.official_booking_label ?? t.doctorCard.bookDoctor}
        </button>
      </div>
    </article>
  );
}
