"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import type {
  ChatTurn,
  InsuranceAdvisorConversationTurn,
  InsuranceAdvisorProfile,
  InsuranceAdvisorRecommendation,
} from "@/lib/types";

const starterPrompt =
  "I am a USC student in 90007 and I want a PPO if possible. My budget is around $350 per month.";

const defaultConversation: InsuranceAdvisorConversationTurn[] = [
  {
    role: "assistant",
    speaker: "Navigator",
    content:
      "Tell me about your coverage path, ZIP code, budget, and how often you expect to use care. I will turn that into a shortlist before you pick doctors.",
  },
];

function toBackendConversation(turns: InsuranceAdvisorConversationTurn[]): ChatTurn[] {
  return turns.map((turn) => ({
    role: turn.role,
    content: `${turn.speaker}: ${turn.content}`,
  }));
}

function confidenceLabelText(value: InsuranceAdvisorRecommendation["confidence_label"]) {
  if (value === "strong") {
    return "Strong fit";
  }
  if (value === "good") {
    return "Good fit";
  }
  return "Early shortlist";
}

function formatCurrency(value?: number | null) {
  if (value === null || value === undefined) {
    return "Varies";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);
}

export function InsuranceAdvisorChat() {
  const router = useRouter();
  const recommendationsRef = useRef<HTMLDivElement | null>(null);
  const initialFlow = useMemo(() => getFlowState(), []);
  const [conversation, setConversation] = useState<InsuranceAdvisorConversationTurn[]>(
    initialFlow.insuranceAdvisorConversation?.length
      ? initialFlow.insuranceAdvisorConversation
      : defaultConversation,
  );
  const [profile, setProfile] = useState<InsuranceAdvisorProfile>(
    initialFlow.insuranceAdvisorProfile ?? {},
  );
  const [profileSummary, setProfileSummary] = useState<string[]>(
    initialFlow.insuranceAdvisorProfileSummary ?? [],
  );
  const [missingFields, setMissingFields] = useState<string[]>(
    initialFlow.insuranceAdvisorMissingFields ?? [],
  );
  const [recommendations, setRecommendations] = useState<InsuranceAdvisorRecommendation[]>(
    initialFlow.insuranceAdvisorRecommendations ?? [],
  );
  const [readinessLabel, setReadinessLabel] = useState<
    "intake" | "narrowing" | "recommended"
  >(initialFlow.insuranceAdvisorReadinessLabel ?? "intake");
  const [disclaimer, setDisclaimer] = useState(
    "This is a planning tool, not official enrollment advice.",
  );
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [message, setMessage] = useState(starterPrompt);
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);

  function persistAdvisorState(next: {
    nextConversation: InsuranceAdvisorConversationTurn[];
    nextProfile: InsuranceAdvisorProfile;
    nextProfileSummary: string[];
    nextMissingFields: string[];
    nextRecommendations: InsuranceAdvisorRecommendation[];
    nextReadinessLabel: "intake" | "narrowing" | "recommended";
  }) {
    patchFlowState({
      insuranceAdvisorConversation: next.nextConversation,
      insuranceAdvisorProfile: next.nextProfile,
      insuranceAdvisorProfileSummary: next.nextProfileSummary,
      insuranceAdvisorMissingFields: next.nextMissingFields,
      insuranceAdvisorRecommendations: next.nextRecommendations,
      insuranceAdvisorReadinessLabel: next.nextReadinessLabel,
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }

    const nextUserTurn: InsuranceAdvisorConversationTurn = {
      role: "user",
      speaker: "You",
      content: message.trim(),
    };
    const optimisticConversation = [...conversation, nextUserTurn];
    setConversation(optimisticConversation);
    setMessage("");
    setError("");
    setIsSending(true);

    try {
      const response = await api.sendInsuranceAdvisorMessage({
        message: nextUserTurn.content,
        conversation: toBackendConversation(optimisticConversation),
        profile,
      });

      const assistantTurns: InsuranceAdvisorConversationTurn[] = response.group_messages.map(
        (item) => ({
          role: "assistant",
          speaker: item.speaker,
          content: item.content,
        }),
      );
      const mergedConversation = [...optimisticConversation, ...assistantTurns];

      setConversation(mergedConversation);
      setProfile(response.profile);
      setProfileSummary(response.profile_summary);
      setMissingFields(response.missing_fields);
      setRecommendations(response.recommendations);
      setReadinessLabel(response.readiness_label);
      setSuggestedPrompts(response.suggested_prompts);
      setDisclaimer(response.disclaimer);

      persistAdvisorState({
        nextConversation: mergedConversation,
        nextProfile: response.profile,
        nextProfileSummary: response.profile_summary,
        nextMissingFields: response.missing_fields,
        nextRecommendations: response.recommendations,
        nextReadinessLabel: response.readiness_label,
      });
    } catch (submissionError) {
      setConversation(conversation);
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to talk to the insurance advisor right now.",
      );
    } finally {
      setIsSending(false);
    }
  }

  function applyRecommendation(recommendation: InsuranceAdvisorRecommendation) {
    patchFlowState({
      insuranceQuery: recommendation.insurance_query,
      insuranceSummary: recommendation.insurance_summary,
      insurancePlanIdOverride:
        recommendation.doctor_search_plan_id ?? recommendation.insurance_summary.plan_id ?? undefined,
      insurancePurchaseUrl: recommendation.purchase_url ?? undefined,
      insuranceAdvisorConversation: conversation,
      insuranceAdvisorProfile: profile,
      insuranceAdvisorProfileSummary: profileSummary,
      insuranceAdvisorMissingFields: missingFields,
      insuranceAdvisorRecommendations: recommendations,
      insuranceAdvisorReadinessLabel: readinessLabel,
      searchResult: undefined,
      selectedDoctor: undefined,
      booking: undefined,
    });
    router.push("/doctors");
  }

  function scrollRecommendations(direction: "left" | "right") {
    if (!recommendationsRef.current) {
      return;
    }
    const offset = direction === "left" ? -380 : 380;
    recommendationsRef.current.scrollBy({ left: offset, behavior: "smooth" });
  }

  return (
    <section className="panel insurance-advisor-panel">
      <div className="panel-heading">
        <span className="eyebrow">AI insurance advisor</span>
        <h2>Talk through plan fit before choosing doctors</h2>
        <p>
          This group-style chat gathers a lightweight insurance profile, narrows
          your plan options, and lets you carry the chosen plan into the doctor
          search flow.
        </p>
      </div>

      <div className="conversation insurance-advisor-conversation">
        {conversation.map((turn, index) => (
          <article
            className={`chat-bubble ${turn.role === "assistant" ? "assistant" : "user"}`}
            key={`${turn.role}-${turn.speaker}-${index}`}
          >
            <strong>{turn.speaker}</strong>
            <ChatMessageContent
              content={turn.content}
              role={turn.role === "assistant" ? "assistant" : "user"}
            />
          </article>
        ))}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          rows={4}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Tell the advisor about your budget, ZIP code, student status, prescriptions, or whether you want PPO flexibility."
        />
        <button className="button button-primary" disabled={isSending} type="submit">
          {isSending ? "Thinking..." : "Send to advisor"}
        </button>
      </form>

      {suggestedPrompts.length ? (
        <div className="suggested-prompts-grid">
          {suggestedPrompts.map((prompt) => (
            <button
              className="chip-button"
              key={prompt}
              onClick={() => setMessage(prompt)}
              type="button"
            >
              {prompt}
            </button>
          ))}
        </div>
      ) : null}

      {error ? <p className="error-text">{error}</p> : null}

      <div className="insurance-advisor-grid">
        <section className="insurance-advisor-summary-card">
          <div className="detail-section-heading">
            <h3>Current profile</h3>
            <span className="meta-pill">{readinessLabel}</span>
          </div>
          {profileSummary.length ? (
            <ul className="detail-list">
              {profileSummary.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted-copy">
              No structured profile yet. Start by sharing your ZIP code, budget,
              and whether you are comparing student or marketplace coverage.
            </p>
          )}

          {missingFields.length ? (
            <>
              <h4>Still helpful to know</h4>
              <ul className="detail-list">
                {missingFields.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          ) : null}

          <p className="insurance-advisor-disclaimer">{disclaimer}</p>
        </section>

        <section className="insurance-advisor-summary-card">
          <div className="detail-section-heading">
            <h3>Recommended plans</h3>
            {recommendations.length ? (
              <span className="meta-pill">{recommendations.length} ready</span>
            ) : null}
          </div>
          {recommendations.length ? (
            <>
              <div className="insurance-advisor-carousel-controls">
                <button
                  aria-label="Scroll left through recommended plans"
                  className="button button-secondary insurance-carousel-button"
                  onClick={() => scrollRecommendations("left")}
                  type="button"
                >
                  ←
                </button>
                <p className="muted-copy insurance-carousel-copy">
                  Swipe or use the arrows to compare plans side by side.
                </p>
                <button
                  aria-label="Scroll right through recommended plans"
                  className="button button-secondary insurance-carousel-button"
                  onClick={() => scrollRecommendations("right")}
                  type="button"
                >
                  →
                </button>
              </div>

              <div className="insurance-advisor-recommendation-list" ref={recommendationsRef}>
                {recommendations.map((recommendation) => (
                  <article className="advisor-recommendation-card" key={recommendation.plan_id}>
                    <div className="advisor-recommendation-header">
                      <div>
                        <h4>
                          {recommendation.provider} {recommendation.plan_name}
                        </h4>
                        <p className="muted-copy advisor-plan-subtitle">
                          {recommendation.metal_level
                            ? `${recommendation.metal_level} · ${recommendation.plan_type}`
                            : recommendation.plan_type}
                        </p>
                        <p>{recommendation.advisor_blurb}</p>
                      </div>
                      <div className="advisor-recommendation-score">
                        <strong>{recommendation.fit_score}</strong>
                        <span>{confidenceLabelText(recommendation.confidence_label)}</span>
                      </div>
                    </div>

                    <div className="document-meta-row advisor-metric-grid">
                      <span className="meta-pill">
                        premium {formatCurrency(recommendation.monthly_premium_amount)}
                      </span>
                      <span className="meta-pill">
                        deductible {formatCurrency(recommendation.deductible_amount)}
                      </span>
                      <span className="meta-pill">
                        OOP max {formatCurrency(recommendation.out_of_pocket_max_amount)}
                      </span>
                      <span className="meta-pill">
                        {recommendation.network_flexibility === "high"
                          ? "more flexible network"
                          : "tighter network"}
                      </span>
                      {recommendation.quality_rating ? (
                        <span className="meta-pill">
                          quality {recommendation.quality_rating.toFixed(1)} / 5
                        </span>
                      ) : null}
                    </div>

                    <h5>Why it fits</h5>
                    <ul className="detail-list">
                      {recommendation.reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>

                    <h5>Tradeoffs</h5>
                    <ul className="detail-list">
                      {recommendation.tradeoffs.map((tradeoff) => (
                        <li key={tradeoff}>{tradeoff}</li>
                      ))}
                    </ul>

                    <div className="advisor-card-actions">
                      <button
                        className="button button-primary"
                        onClick={() => applyRecommendation(recommendation)}
                        type="button"
                      >
                        Use this plan for doctor search
                      </button>
                      {recommendation.purchase_url ? (
                        <a
                          className="button button-secondary"
                          href={recommendation.purchase_url}
                          rel="noreferrer"
                          target="_blank"
                        >
                          {recommendation.purchase_cta_label ?? "Official purchase link"}
                        </a>
                      ) : null}
                      {recommendation.source_url ? (
                        <a
                          className="button button-secondary"
                          href={recommendation.source_url}
                          rel="noreferrer"
                          target="_blank"
                        >
                          Plan details
                        </a>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            </>
          ) : (
            <p className="muted-copy">
              Recommendations will appear once the advisor has enough detail to
              narrow the catalog down responsibly.
            </p>
          )}
        </section>
      </div>
    </section>
  );
}
