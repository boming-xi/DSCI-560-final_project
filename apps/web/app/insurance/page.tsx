"use client";

import { useMemo, useState } from "react";

import { InsuranceAdvisorChat } from "@/components/InsuranceAdvisorChat";
import { InsuranceUpload } from "@/components/InsuranceUpload";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import { useProtectedRoute } from "@/lib/useProtectedRoute";

export default function InsurancePage() {
  const { t } = useTranslation();
  const { isCheckingAuth, session } = useProtectedRoute();
  const initialFlow = useMemo(() => getFlowState(), []);
  const [entryMode, setEntryMode] = useState<"has_insurance" | "needs_help" | null>(() => {
    if (initialFlow.insuranceEntryMode) {
      return initialFlow.insuranceEntryMode;
    }
    if (initialFlow.insuranceSummary || initialFlow.insuranceQuery) {
      return "has_insurance";
    }
    if (
      initialFlow.insuranceAdvisorConversation?.length ||
      initialFlow.insuranceAdvisorRecommendations?.length
    ) {
      return "needs_help";
    }
    return null;
  });

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">{t.insurance.authLoading}</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  function chooseMode(mode: "has_insurance" | "needs_help") {
    setEntryMode(mode);
    patchFlowState({ insuranceEntryMode: mode });
  }

  return (
    <main className="page-shell">
      <section className="panel insurance-guidance-panel">
        <div className="insurance-guidance-copy">
          <span className="eyebrow">{t.insurance.pageLabel}</span>
          <h1>{t.insurance.pageTitle}</h1>
          <p>{t.insurance.pageSubtitle}</p>
        </div>

        <div className="insurance-guidance-grid">
          {t.insurance.pageProofs.map((proof) => (
            <article className="insurance-guidance-card" key={proof.title}>
              <h3>{proof.title}</h3>
              <p>{proof.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel insurance-entry-panel">
        <div className="panel-heading">
          <span className="eyebrow">{t.insurance.step1}</span>
          <h2>{t.insurance.choosePathTitle}</h2>
          <p>{t.insurance.choosePathSubtitle}</p>
        </div>

        <div className="insurance-entry-grid">
          <button
            className={`insurance-entry-card ${entryMode === "has_insurance" ? "active" : ""}`}
            onClick={() => chooseMode("has_insurance")}
            type="button"
          >
            <span className="meta-pill">{t.insurance.hasInsurancePill}</span>
            <h3>{t.insurance.hasInsuranceTitle}</h3>
            <p>{t.insurance.hasInsuranceBody}</p>
          </button>

          <button
            className={`insurance-entry-card ${entryMode === "needs_help" ? "active" : ""}`}
            onClick={() => chooseMode("needs_help")}
            type="button"
          >
            <span className="meta-pill">{t.insurance.needsHelpPill}</span>
            <h3>{t.insurance.needsHelpTitle}</h3>
            <p>{t.insurance.needsHelpBody}</p>
          </button>
        </div>
      </section>

      {entryMode ? (
        <div className="insurance-step-stack">
          <div className="insurance-step-toolbar">
            <p className="muted-copy">
              {entryMode === "has_insurance"
                ? t.insurance.existingModeNotice
                : t.insurance.advisorModeNotice}
            </p>
            <button
              className="button button-secondary"
              onClick={() =>
                chooseMode(entryMode === "has_insurance" ? "needs_help" : "has_insurance")
              }
              type="button"
            >
              {entryMode === "has_insurance"
                ? t.insurance.switchToAdvisor
                : t.insurance.switchToUpload}
            </button>
          </div>

          {entryMode === "has_insurance" ? <InsuranceUpload /> : <InsuranceAdvisorChat />}
        </div>
      ) : (
        <section className="panel notice-box">
          <strong>{t.insurance.step2PendingTitle}</strong>
          <p>{t.insurance.step2PendingBody}</p>
        </section>
      )}
    </main>
  );
}
