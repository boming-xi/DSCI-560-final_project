"use client";

import type { DoctorProfile } from "@/lib/types";

type DoctorCardProps = {
  doctor: DoctorProfile;
  highlighted?: boolean;
  onBook: () => void;
  onView: () => void;
};

export function DoctorCard({
  doctor,
  highlighted = false,
  onBook,
  onView,
}: DoctorCardProps) {
  return (
    <article className={`panel doctor-card ${highlighted ? "recommended-card" : ""}`}>
      <div className="doctor-card-top">
        <div>
          <span className="eyebrow">{doctor.specialty}</span>
          {highlighted ? <span className="recommended-doctor-tag">Advisor pick</span> : null}
          <h3>{doctor.name}</h3>
          <p>{doctor.profile_blurb}</p>
        </div>
        <div className="score-badge">
          <strong>{doctor.ranking_breakdown?.total_score ?? 0}</strong>
          <span>match score</span>
        </div>
      </div>

      <div className="badge-row">
        <span className="badge">{doctor.years_experience} yrs experience</span>
        <span className="badge">{doctor.distance_km} km away</span>
        <span className="badge">{doctor.rating} rating</span>
        <span className="badge">{doctor.next_opening_label}</span>
        <span className="badge">
          {doctor.availability_days === 0
            ? "Same-day availability"
            : `Available in ${doctor.availability_days} days`}
        </span>
      </div>

      {doctor.clinical_focus.length ? (
        <div className="doctor-focus-preview">
          <h4>Good fit for</h4>
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
          <h4>Clinic</h4>
          <p>{doctor.clinic.name}</p>
          <p>{doctor.clinic.address}</p>
        </div>
        <div>
          <h4>Languages</h4>
          <p>{doctor.languages.join(", ")}</p>
        </div>
        <div>
          <h4>Network verification</h4>
          <p>{doctor.insurance_verification?.label ?? "No plan selected yet"}</p>
          <p className="subtle-copy">
            {doctor.insurance_verification?.reason ?? "Choose an insurance plan to verify network fit."}
          </p>
        </div>
        <div>
          <h4>Estimated cost</h4>
          <p>
            {doctor.estimated_cost ? `$${doctor.estimated_cost} copay estimate` : "Plan needed"}
          </p>
        </div>
      </div>

      {doctor.insurance_verification?.network_url ? (
        <div className="info-box">
          <strong>{doctor.insurance_verification.label}</strong>
          <p>{doctor.insurance_verification.reason}</p>
          <a href={doctor.insurance_verification.network_url} rel="noreferrer" target="_blank">
            Open official network directory
          </a>
        </div>
      ) : null}

      {doctor.referral_required ? (
        <div className="notice-box">
          Referral may be required before this specialist appointment.
        </div>
      ) : null}

      <div className="form-actions">
        <button className="button button-secondary" onClick={onView} type="button">
          View full profile
        </button>
        <button className="button button-primary" onClick={onBook} type="button">
          Book this doctor
        </button>
      </div>
    </article>
  );
}
