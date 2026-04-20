"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { DoctorDecisionChat } from "@/components/DoctorDecisionChat";
import { DoctorCard } from "@/components/DoctorCard";
import { RankingExplanation } from "@/components/RankingExplanation";
import { api } from "@/lib/api";
import { beginDoctorBooking } from "@/lib/doctor-booking";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import type { DoctorSearchResponse } from "@/lib/types";

export default function DoctorsPage() {
  const router = useRouter();
  const { isCheckingAuth, session } = useProtectedRoute();
  const flow = getFlowState();
  const [result, setResult] = useState<DoctorSearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [recommendedDoctorId, setRecommendedDoctorId] = useState(
    flow.doctorDecisionRecommendedDoctorId ?? "",
  );

  useEffect(() => {
    async function loadDoctors() {
      if (isCheckingAuth || !session) {
        return;
      }
      const flow = getFlowState();
      if (!flow.symptomText || !flow.location) {
        setError("Start with symptoms first so we can narrow the right doctors for you.");
        setIsLoading(false);
        return;
      }

      try {
        const searchResult = await api.searchDoctors({
          symptom_text: flow.symptomText,
          insurance_query: flow.insuranceQuery || undefined,
          insurance_selected_plan_id: flow.insuranceSummary?.plan_id || undefined,
          insurance_plan_id_override: flow.insurancePlanIdOverride || undefined,
          location: flow.location,
          preferred_language: flow.preferredLanguage,
          duration_days: 1,
          top_k: 5,
        });

        patchFlowState({ searchResult });
        setResult(searchResult);
        setRecommendedDoctorId("");
      } catch (searchError) {
        setError(
          searchError instanceof Error
            ? searchError.message
            : "We could not build the doctor shortlist just yet."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDoctors();
  }, [isCheckingAuth, session]);

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Preparing your doctor shortlist...</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  function handleBookDoctor(doctorId: string) {
    const flow = getFlowState();
    const selectedDoctor =
      flow.searchResult?.doctors.find((doctor) => doctor.id === doctorId) ??
      result?.doctors.find((doctor) => doctor.id === doctorId);

    if (!selectedDoctor) {
      return;
    }

    beginDoctorBooking(selectedDoctor, {
      onInternalBooking: () => router.push("/booking"),
    });
  }

  function handleViewDoctor(doctorId: string) {
    const flow = getFlowState();
    const selectedDoctor =
      flow.searchResult?.doctors.find((doctor) => doctor.id === doctorId) ??
      result?.doctors.find((doctor) => doctor.id === doctorId);

    if (selectedDoctor) {
      patchFlowState({ selectedDoctor });
    }
    router.push(`/doctors/${doctorId}`);
  }

  return (
    <main className="page-shell">
      <section className="results-header panel">
        <span className="eyebrow">Step 3</span>
        <h1>Ranked doctor and clinic recommendations</h1>
        <p>
          The list below balances specialty match, insurance, distance,
          availability, language, and trust signals.
        </p>
      </section>

      {isLoading ? <div className="panel">Building your ranked doctor shortlist...</div> : null}
      {error ? <div className="panel error-panel">{error}</div> : null}

      {result ? (
        <>
          <section className="summary-grid">
            <article className="panel summary-card">
              <span className="eyebrow">Triage</span>
              <h2>{result.triage.urgency_level}</h2>
              <p>{result.triage.summary}</p>
              <p>{result.triage.next_step}</p>
            </article>
            <article className="panel summary-card">
              <span className="eyebrow">Insurance</span>
              <h2>
                {flow.insuranceSummary?.matched
                  ? `${flow.insuranceSummary.provider} ${flow.insuranceSummary.plan_name}`
                  : result.insurance_summary?.matched
                  ? `${result.insurance_summary.provider} ${result.insurance_summary.plan_name}`
                  : "Plan not attached yet"}
              </h2>
              <p>
                {flow.insuranceSummary?.notes?.[0] ??
                  result.insurance_summary?.notes?.[0] ??
                  "Doctor ranking is currently based on symptoms, location, and clinician fit."}
              </p>
              {flow.insuranceNetworkUrl ? (
                <p>
                  <a href={flow.insuranceNetworkUrl} rel="noreferrer" target="_blank">
                    Open official network directory
                  </a>
                </p>
              ) : null}
            </article>
          </section>

          {result.doctors[0] ? (
            <RankingExplanation doctors={result.doctors.slice(0, 3)} />
          ) : null}

          <DoctorDecisionChat
            doctors={result.doctors}
            insuranceQuery={flow.insuranceQuery}
            onAcceptRecommendation={handleBookDoctor}
            onRecommendationChange={(doctorId) => setRecommendedDoctorId(doctorId ?? "")}
            preferredLanguage={flow.preferredLanguage}
            symptomText={flow.symptomText}
          />

          <section className="doctor-list">
            {result.doctors.map((doctor, index) => (
              <DoctorCard
                doctor={doctor}
                highlighted={doctor.id === recommendedDoctorId}
                key={doctor.id}
                rank={index + 1}
                onBook={() => handleBookDoctor(doctor.id)}
                onView={() => handleViewDoctor(doctor.id)}
              />
            ))}
          </section>
        </>
      ) : null}
    </main>
  );
}
