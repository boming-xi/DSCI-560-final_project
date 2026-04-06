"use client";

import type { DoctorProfile } from "@/lib/types";

type DoctorCardProps = {
  doctor: DoctorProfile;
  onBook: () => void;
};

export function DoctorCard({ doctor, onBook }: DoctorCardProps) {
  return (
    <article className="panel doctor-card">
      <div className="doctor-card-top">
        <div>
          <span className="eyebrow">{doctor.specialty}</span>
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
        <span className="badge">
          {doctor.availability_days === 0
            ? "Same-day availability"
            : `Available in ${doctor.availability_days} days`}
        </span>
      </div>

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
          <h4>Coverage</h4>
          <p>{doctor.accepted_insurance.join(", ")}</p>
        </div>
        <div>
          <h4>Estimated cost</h4>
          <p>
            {doctor.estimated_cost ? `$${doctor.estimated_cost} copay estimate` : "Plan needed"}
          </p>
        </div>
      </div>

      {doctor.referral_required ? (
        <div className="notice-box">
          Referral may be required before this specialist appointment.
        </div>
      ) : null}

      <div className="form-actions">
        <button className="button button-primary" onClick={onBook} type="button">
          Book this doctor
        </button>
      </div>
    </article>
  );
}
