"use client";

import { useMemo, useState } from "react";

import { useTranslation } from "@/lib/LanguageProvider";
import type { DoctorProfile, InsuranceSummary, TriageRecommendation } from "@/lib/types";

type CarePassportCardProps = {
  symptomText?: string;
  triage?: TriageRecommendation;
  insuranceSummary?: InsuranceSummary;
  doctor?: DoctorProfile | null;
  insuranceQuery?: string;
  bookingUrl?: string | null;
};

type PassportTextProps = CarePassportCardProps & {
  t: ReturnType<typeof useTranslation>["t"];
};

function buildPassportText({
  symptomText,
  triage,
  insuranceSummary,
  doctor,
  insuranceQuery,
  bookingUrl,
  t,
}: PassportTextProps): string {
  const insuranceLine = insuranceSummary?.matched
    ? `${insuranceSummary.provider} ${insuranceSummary.plan_name}`
    : insuranceQuery?.trim()
      ? t.carePassport.insuranceEnteredForReview.replace("{query}", insuranceQuery.trim())
      : t.carePassport.noPlanAttached;

  const doctorLine = doctor
    ? `${doctor.name}, ${doctor.specialty}, ${doctor.clinic.name}`
    : t.carePassport.doctorNotChosen;

  return [
    t.carePassport.textTitle,
    "",
    `${t.carePassport.textSymptoms}: ${symptomText?.trim() || t.carePassport.notProvided}`,
    `${t.carePassport.textCarePath}: ${triage?.care_type || t.carePassport.notAvailableYet}`,
    `${t.carePassport.textUrgencyBand}: ${
      triage?.urgency_level || t.carePassport.notAvailableYet
    }`,
    `${t.carePassport.textInsuranceStatus}: ${insuranceLine}`,
    `${t.carePassport.textRecommendedDoctor}: ${doctorLine}`,
    `${t.carePassport.textNetworkCheck}: ${
      doctor?.insurance_verification?.label || t.carePassport.pending
    }`,
    `${t.carePassport.textOfficialBookingLink}: ${
      bookingUrl || doctor?.official_booking_url || t.carePassport.notAttached
    }`,
  ].join("\n");
}

export function CarePassportCard(props: CarePassportCardProps) {
  const { t } = useTranslation();
  const [feedback, setFeedback] = useState("");

  const passportText = useMemo(
    () => buildPassportText({ ...props, t }),
    [props, t],
  );

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(passportText);
      setFeedback(t.carePassport.copied);
    } catch {
      setFeedback(t.carePassport.copyUnavailable);
    }
  }

  async function handleShare() {
    if (!navigator.share) {
      await handleCopy();
      return;
    }

    try {
      await navigator.share({
        title: t.carePassport.title,
        text: passportText,
        url: props.bookingUrl || props.doctor?.official_booking_url || undefined,
      });
      setFeedback(t.carePassport.shared);
    } catch {
      setFeedback("");
    }
  }

  return (
    <section className="panel care-passport-card">
      <div className="care-passport-header">
        <div>
          <span className="eyebrow">{t.carePassport.title}</span>
          <h2>{t.carePassport.heading}</h2>
          <p>{t.carePassport.subtitle}</p>
        </div>
        <div className="form-actions">
          <button className="button button-secondary" onClick={handleCopy} type="button">
            {t.carePassport.copySummary}
          </button>
          <button className="button button-primary" onClick={handleShare} type="button">
            {t.carePassport.shareSummary}
          </button>
        </div>
      </div>

      <div className="care-passport-grid">
        <article className="care-passport-item">
          <span className="eyebrow">{t.carePassport.symptoms}</span>
          <h3>{props.triage?.summary ?? t.carePassport.symptomPending}</h3>
          <p>{props.symptomText ?? t.carePassport.addSymptoms}</p>
        </article>

        <article className="care-passport-item">
          <span className="eyebrow">{t.carePassport.carePath}</span>
          <h3>{props.triage?.care_type ?? t.carePassport.carePathPending}</h3>
          <p>{props.triage?.next_step ?? t.carePassport.carePathAppears}</p>
        </article>

        <article className="care-passport-item">
          <span className="eyebrow">{t.carePassport.insuranceStatus}</span>
          <h3>
            {props.insuranceSummary?.matched
              ? `${props.insuranceSummary.provider} ${props.insuranceSummary.plan_name}`
              : props.insuranceQuery?.trim() || t.carePassport.noPlanAttached}
          </h3>
          <p>{props.insuranceSummary?.notes?.[0] ?? t.carePassport.insuranceAppears}</p>
        </article>

        <article className="care-passport-item">
          <span className="eyebrow">{t.carePassport.recommendedDoctor}</span>
          <h3>{props.doctor?.name ?? t.carePassport.doctorNotChosen}</h3>
          <p>
            {props.doctor
              ? `${props.doctor.specialty} at ${props.doctor.clinic.name}`
              : t.carePassport.chooseDoctor}
          </p>
        </article>
      </div>

      {feedback ? <p className="muted-copy">{feedback}</p> : null}
    </section>
  );
}
