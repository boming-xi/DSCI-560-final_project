"use client";

import { useMemo, useState } from "react";

import { InsuranceAdvisorChat } from "@/components/InsuranceAdvisorChat";
import { InsuranceUpload } from "@/components/InsuranceUpload";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";

export default function InsurancePage() {
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
        <div className="panel">Checking your account before opening insurance...</div>
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
      <section className="panel insurance-entry-panel">
        <div className="panel-heading">
          <span className="eyebrow">Step 1</span>
          <h2>Choose your insurance path</h2>
          <p>
            If you already have a plan, we can parse it and move straight into
            doctor search. If you do not have insurance yet, the advisor can
            help you narrow plans first.
          </p>
        </div>

        <div className="insurance-entry-grid">
          <button
            className={`insurance-entry-card ${entryMode === "has_insurance" ? "active" : ""}`}
            onClick={() => chooseMode("has_insurance")}
            type="button"
          >
            <span className="meta-pill">I already have insurance</span>
            <h3>Upload or paste my current plan</h3>
            <p>
              Best when you have an insurance card, portal screenshot, plan PDF,
              or already know the plan name you want to use.
            </p>
          </button>

          <button
            className={`insurance-entry-card ${entryMode === "needs_help" ? "active" : ""}`}
            onClick={() => chooseMode("needs_help")}
            type="button"
          >
            <span className="meta-pill">I need help choosing insurance</span>
            <h3>Compare plans with the AI advisor</h3>
            <p>
              Best when you want help thinking through budget, PPO vs HMO,
              referrals, prescriptions, and plan tradeoffs before choosing
              doctors.
            </p>
          </button>
        </div>
      </section>

      {entryMode ? (
        <div className="insurance-step-stack">
          <div className="insurance-step-toolbar">
            <p className="muted-copy">
              {entryMode === "has_insurance"
                ? "Step 2 is set to existing insurance upload. You can switch paths anytime."
                : "Step 2 is set to insurance advisor. You can switch paths anytime."}
            </p>
            <button
              className="button button-secondary"
              onClick={() =>
                chooseMode(entryMode === "has_insurance" ? "needs_help" : "has_insurance")
              }
              type="button"
            >
              {entryMode === "has_insurance"
                ? "Switch to plan advisor"
                : "Switch to existing insurance upload"}
            </button>
          </div>

          {entryMode === "has_insurance" ? <InsuranceUpload /> : <InsuranceAdvisorChat />}
        </div>
      ) : (
        <section className="panel notice-box">
          <strong>Step 2 opens after you choose a path.</strong>
          <p>
            Pick whether you already have insurance or need help choosing one,
            and we will keep the rest of the flow focused on that path.
          </p>
        </section>
      )}
    </main>
  );
}
