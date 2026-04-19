"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { DoctorCard } from "@/components/DoctorCard";
import { RankingExplanation } from "@/components/RankingExplanation";
import { api } from "@/lib/api";
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

  useEffect(() => {
    async function loadDoctors() {
      if (isCheckingAuth || !session) {
        return;
      }
      const flow = getFlowState();
      if (!flow.symptomText || !flow.location) {
        setError("Please complete the symptom step first.");
        setIsLoading(false);
        return;
      }

      try {
        const searchResult = await api.searchDoctors({
          symptom_text: flow.symptomText,
          insurance_query: flow.insuranceQuery || undefined,
          insurance_plan_id_override: flow.insurancePlanIdOverride || undefined,
          location: flow.location,
          preferred_language: flow.preferredLanguage,
          duration_days: flow.durationDays ?? 1,
          top_k: 5,
        });

        patchFlowState({ searchResult });
        setResult(searchResult);
      } catch (searchError) {
        setError(
          searchError instanceof Error
            ? searchError.message
            : "Unable to load doctor recommendations."
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
        <div className="panel">Checking your account before opening doctor search...</div>
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

    patchFlowState({ selectedDoctor });
    router.push("/booking");
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

      {isLoading ? <div className="panel">Loading ranked doctor matches...</div> : null}
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
                  : "No matched plan"}
              </h2>
              <p>
                {flow.insuranceSummary?.notes?.[0] ??
                  result.insurance_summary?.notes?.[0] ??
                  "Browsing without insurance filter."}
              </p>
            </article>
          </section>

          {result.doctors[0] ? <RankingExplanation doctor={result.doctors[0]} /> : null}

          <section className="doctor-list">
            {result.doctors.map((doctor) => (
              <DoctorCard
                doctor={doctor}
                key={doctor.id}
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
