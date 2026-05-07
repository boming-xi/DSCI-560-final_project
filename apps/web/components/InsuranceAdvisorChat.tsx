"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type {
  ChatTurn,
  InsuranceAdvisorConversationTurn,
  InsuranceAdvisorProfile,
  InsuranceAdvisorRecommendation,
} from "@/lib/types";

function toBackendConversation(turns: InsuranceAdvisorConversationTurn[]): ChatTurn[] {
  return turns.map((turn) => ({
    role: turn.role,
    content: `${turn.speaker}: ${turn.content}`,
  }));
}

function confidenceLabelText(
  value: InsuranceAdvisorRecommendation["confidence_label"],
  t: ReturnType<typeof useTranslation>["t"],
) {
  if (value === "strong") {
    return t.insurance.strongFit;
  }
  if (value === "good") {
    return t.insurance.goodFit;
  }
  return t.insurance.earlyShortlist;
}

function readinessLabelText(
  value: "intake" | "narrowing" | "recommended",
  t: ReturnType<typeof useTranslation>["t"],
) {
  if (value === "recommended") {
    return t.insurance.readinessRecommended;
  }
  if (value === "narrowing") {
    return t.insurance.readinessNarrowing;
  }
  return t.insurance.readinessIntake;
}

function formatCurrency(
  value: number | null | undefined,
  locale: string,
  variesLabel: string,
) {
  if (value === null || value === undefined) {
    return variesLabel;
  }
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);
}

function normalizeRecommendation(
  recommendation: Partial<InsuranceAdvisorRecommendation>,
): InsuranceAdvisorRecommendation {
  const nestedPlans = Array.isArray(recommendation.more_plans)
    ? recommendation.more_plans.map((item) => normalizeRecommendation(item))
    : [];

  return {
    ...(recommendation as InsuranceAdvisorRecommendation),
    available_plan_count:
      typeof recommendation.available_plan_count === "number"
        ? recommendation.available_plan_count
        : Math.max(1, nestedPlans.length + 1),
    more_plans: nestedPlans,
  };
}

function normalizeRecommendations(
  recommendations?: InsuranceAdvisorRecommendation[],
): InsuranceAdvisorRecommendation[] {
  if (!Array.isArray(recommendations)) {
    return [];
  }
  return recommendations.map((item) => normalizeRecommendation(item));
}

export function InsuranceAdvisorChat() {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const advisorLocale =
    lang === "Mandarin" ? "zh-CN" : lang === "Spanish" ? "es-ES" : "en-US";
  const defaultConversation = useMemo<InsuranceAdvisorConversationTurn[]>(
    () => [
      {
        role: "assistant",
        speaker: t.insurance.navigatorSpeaker,
        content:
          lang === "Mandarin"
            ? "请先告诉我你的保险路径、邮编、预算，以及你预计会多频繁使用医疗服务。我会在你选医生前，先把它缩小成一个更可解释的计划候选列表。"
            : lang === "Spanish"
            ? "Cuéntame tu ruta de cobertura, código postal, presupuesto y con qué frecuencia esperas usar atención médica. Lo convertiré en una lista corta antes de que elijas doctores."
            : "Tell me about your coverage path, ZIP code, budget, and how often you expect to use care. I will turn that into a shortlist before you pick doctors.",
      },
    ],
    [lang, t.insurance.navigatorSpeaker],
  );
  const initialRecommendations = useMemo(
    () => normalizeRecommendations(initialFlow.insuranceAdvisorRecommendations),
    [initialFlow],
  );
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
    initialRecommendations,
  );
  const [readinessLabel, setReadinessLabel] = useState<
    "intake" | "narrowing" | "recommended"
  >(initialFlow.insuranceAdvisorReadinessLabel ?? "intake");
  const [disclaimer, setDisclaimer] = useState<string>(
    t.insurance.disclaimer,
  );
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showAdvisorHint, setShowAdvisorHint] = useState(true);
  const [expandedProviders, setExpandedProviders] = useState<Record<string, boolean>>({});

  function persistAdvisorState(next: {
    nextConversation: InsuranceAdvisorConversationTurn[];
    nextProfile: InsuranceAdvisorProfile;
    nextProfileSummary: string[];
    nextMissingFields: string[];
    nextRecommendations: InsuranceAdvisorRecommendation[];
    nextReadinessLabel: "intake" | "narrowing" | "recommended";
  }) {
    patchFlowState({
      insuranceEntryMode: "needs_help",
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
      speaker: t.insurance.userSpeaker,
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
        ui_language: lang,
      });

      const assistantTurns: InsuranceAdvisorConversationTurn[] = response.group_messages.map(
        (item) => ({
          role: "assistant",
          speaker: item.speaker,
          content: item.content,
        }),
      );
      const mergedConversation = [...optimisticConversation, ...assistantTurns];
      const normalizedRecommendations = normalizeRecommendations(response.recommendations);

      setConversation(mergedConversation);
      setProfile(response.profile);
      setProfileSummary(response.profile_summary);
      setMissingFields(response.missing_fields);
      setRecommendations(normalizedRecommendations);
      setReadinessLabel(response.readiness_label);
      setDisclaimer(response.disclaimer);

      persistAdvisorState({
        nextConversation: mergedConversation,
        nextProfile: response.profile,
        nextProfileSummary: response.profile_summary,
        nextMissingFields: response.missing_fields,
        nextRecommendations: normalizedRecommendations,
        nextReadinessLabel: response.readiness_label,
      });
    } catch (submissionError) {
      setConversation(conversation);
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : t.insurance.reviewError,
      );
    } finally {
      setIsSending(false);
    }
  }

  function applyRecommendation(recommendation: InsuranceAdvisorRecommendation) {
    patchFlowState({
      insuranceEntryMode: "needs_help",
      insuranceQuery: recommendation.insurance_query,
      insuranceSummary: recommendation.insurance_summary,
      insurancePlanIdOverride:
        recommendation.doctor_search_plan_id ?? recommendation.insurance_summary.plan_id ?? undefined,
      insurancePurchaseUrl: recommendation.purchase_url ?? undefined,
      insuranceNetworkUrl: recommendation.network_url ?? undefined,
      insuranceAdvisorConversation: conversation,
      insuranceAdvisorProfile: profile,
      insuranceAdvisorProfileSummary: profileSummary,
      insuranceAdvisorMissingFields: missingFields,
      insuranceAdvisorRecommendations: recommendations,
      insuranceAdvisorReadinessLabel: readinessLabel,
      searchResult: undefined,
      selectedDoctor: undefined,
    });
    router.push("/doctors");
  }

  function toggleProviderPlans(recommendation: InsuranceAdvisorRecommendation) {
    setExpandedProviders((current) => ({
      ...current,
      [recommendation.plan_id]: !current[recommendation.plan_id],
    }));
  }

  return (
    <section className="panel insurance-advisor-panel">
      <div className="panel-heading">
        <span className="eyebrow">{t.insurance.advisorStep}</span>
        <h2>{t.insurance.advisorTitle}</h2>
        <p>{t.insurance.advisorSubtitle}</p>
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
          onFocus={() => setShowAdvisorHint(false)}
          onBlur={() => setShowAdvisorHint(!message.trim())}
          placeholder={showAdvisorHint ? t.insurance.advisorHint : ""}
        />
        <button className="button button-primary" disabled={isSending} type="submit">
          {isSending ? t.insurance.advisorReviewing : t.insurance.advisorAskButton}
        </button>
      </form>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="insurance-advisor-stack">
        <section className="insurance-advisor-summary-card insurance-advisor-profile-card">
          <div className="detail-section-heading">
            <h3>{t.insurance.currentProfile}</h3>
            <span className="meta-pill">{readinessLabelText(readinessLabel, t)}</span>
          </div>
          {profileSummary.length ? (
            <ul className="detail-list">
              {profileSummary.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted-copy">
              {t.insurance.profileEmpty}
            </p>
          )}

          {missingFields.length ? (
            <>
              <h4>{t.insurance.stillHelpful}</h4>
              <ul className="detail-list">
                {missingFields.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          ) : null}

          <p className="insurance-advisor-disclaimer">{disclaimer}</p>
        </section>

        <section className="insurance-advisor-summary-card insurance-advisor-recommendations-card">
          <div className="detail-section-heading">
            <h3>{t.insurance.recommendedBrands}</h3>
            {recommendations.length ? (
              <span className="meta-pill">
                {recommendations.length} {t.insurance.carriersReady}
              </span>
            ) : null}
          </div>
          {recommendations.length ? (
            <>
              <div className="insurance-advisor-recommendation-list">
                {recommendations.map((recommendation) => (
                  <article className="advisor-recommendation-card" key={recommendation.plan_id}>
                    <div className="advisor-recommendation-header">
                      <div>
                        <h4>{recommendation.provider}</h4>
                        <p className="muted-copy advisor-plan-subtitle">
                          {t.insurance.bestFitPlan}: {recommendation.plan_name}
                          {recommendation.metal_level
                            ? ` · ${recommendation.metal_level}`
                            : ""}
                          {recommendation.plan_type ? ` · ${recommendation.plan_type}` : ""}
                        </p>
                        <p>{recommendation.advisor_blurb}</p>
                      </div>
                    </div>

                    <div className="advisor-recommendation-fit-row">
                      <div className="advisor-recommendation-score">
                        <strong>{recommendation.fit_score}</strong>
                        <span>{confidenceLabelText(recommendation.confidence_label, t)}</span>
                      </div>
                      <span className="meta-pill">
                        {recommendation.available_plan_count}{" "}
                        {recommendation.available_plan_count === 1
                          ? t.insurance.planSingular
                          : t.insurance.planPlural}{" "}
                        {t.insurance.inCarrierShortlist}
                      </span>
                    </div>

                    <div className="document-meta-row advisor-metric-grid">
                      <span className="meta-pill">
                        {t.insurance.premium}{" "}
                        {formatCurrency(
                          recommendation.monthly_premium_amount,
                          advisorLocale,
                          t.insurance.varies,
                        )}
                      </span>
                      <span className="meta-pill">
                        {t.insurance.deductible}{" "}
                        {formatCurrency(
                          recommendation.deductible_amount,
                          advisorLocale,
                          t.insurance.varies,
                        )}
                      </span>
                      <span className="meta-pill">
                        {t.insurance.oopMax}{" "}
                        {formatCurrency(
                          recommendation.out_of_pocket_max_amount,
                          advisorLocale,
                          t.insurance.varies,
                        )}
                      </span>
                      <span className="meta-pill">
                        {recommendation.network_flexibility === "high"
                          ? t.insurance.flexibleNetwork
                          : t.insurance.tighterNetwork}
                      </span>
                      {recommendation.quality_rating ? (
                        <span className="meta-pill">
                          {t.insurance.quality} {recommendation.quality_rating.toFixed(1)} / 5
                        </span>
                      ) : null}
                      {recommendation.network_name ? (
                        <span className="meta-pill">{recommendation.network_name}</span>
                      ) : null}
                    </div>

                    <h5>{t.insurance.whyStrongStartingPoint}</h5>
                    <ul className="detail-list">
                      {recommendation.reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>

                    <h5>{t.insurance.tradeoffs}</h5>
                    <ul className="detail-list">
                      {recommendation.tradeoffs.map((tradeoff) => (
                        <li key={tradeoff}>{tradeoff}</li>
                      ))}
                    </ul>

                    {recommendation.more_plans?.length ? (
                      <div className="advisor-more-plans">
                        <button
                          className="button button-secondary"
                          onClick={() => toggleProviderPlans(recommendation)}
                          type="button"
                        >
                          {expandedProviders[recommendation.plan_id]
                            ? t.insurance.hidePlans.replace(
                                "{provider}",
                                recommendation.provider,
                              )
                            : t.insurance.viewMorePlans.replace(
                                "{provider}",
                                recommendation.provider,
                              )}
                        </button>

                        {expandedProviders[recommendation.plan_id] ? (
                          <div className="advisor-more-plans-list">
                            {recommendation.more_plans.map((planOption) => (
                              <article className="advisor-more-plan-card" key={planOption.plan_id}>
                                <div className="advisor-more-plan-header">
                                  <div>
                                    <h6>{planOption.plan_name}</h6>
                                    <p className="muted-copy">
                                      {planOption.metal_level
                                        ? `${planOption.metal_level} · ${planOption.plan_type}`
                                        : planOption.plan_type}
                                    </p>
                                  </div>
                                  <div className="advisor-more-plan-score">
                                    <strong>{planOption.fit_score}</strong>
                                    <span>{confidenceLabelText(planOption.confidence_label, t)}</span>
                                  </div>
                                </div>
                                <div className="document-meta-row advisor-metric-grid">
                                  <span className="meta-pill">
                                    {t.insurance.premium}{" "}
                                    {formatCurrency(
                                      planOption.monthly_premium_amount,
                                      advisorLocale,
                                      t.insurance.varies,
                                    )}
                                  </span>
                                  <span className="meta-pill">
                                    {t.insurance.deductible}{" "}
                                    {formatCurrency(
                                      planOption.deductible_amount,
                                      advisorLocale,
                                      t.insurance.varies,
                                    )}
                                  </span>
                                  <span className="meta-pill">
                                    {t.insurance.oopMax}{" "}
                                    {formatCurrency(
                                      planOption.out_of_pocket_max_amount,
                                      advisorLocale,
                                      t.insurance.varies,
                                    )}
                                  </span>
                                  {planOption.network_name ? (
                                    <span className="meta-pill">{planOption.network_name}</span>
                                  ) : null}
                                </div>
                                <p className="muted-copy advisor-more-plan-copy">
                                  {planOption.advisor_blurb}
                                </p>
                                <div className="advisor-card-actions">
                                  <button
                                    className="button button-secondary"
                                    onClick={() => applyRecommendation(planOption)}
                                    type="button"
                                  >
                                    {t.insurance.useThisPlanInstead}
                                  </button>
                                  {planOption.source_url ? (
                                    <a
                                      className="button button-secondary"
                                      href={planOption.source_url}
                                      rel="noreferrer"
                                      target="_blank"
                                    >
                                      {t.insurance.planDetails}
                                    </a>
                                  ) : null}
                                </div>
                              </article>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ) : null}

                    <div className="advisor-card-actions">
                      <button
                        className="button button-primary"
                        onClick={() => applyRecommendation(recommendation)}
                        type="button"
                      >
                        {t.insurance.useBestFitPlan}
                      </button>
                      {recommendation.purchase_url ? (
                        <a
                          className="button button-secondary"
                          href={recommendation.purchase_url}
                          rel="noreferrer"
                          target="_blank"
                        >
                          {recommendation.purchase_cta_label ?? t.insurance.officialPurchaseLink}
                        </a>
                      ) : null}
                      {recommendation.source_url ? (
                        <a
                          className="button button-secondary"
                          href={recommendation.source_url}
                          rel="noreferrer"
                          target="_blank"
                        >
                          {t.insurance.planDetails}
                        </a>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            </>
          ) : (
            <p className="muted-copy">
              {t.insurance.recommendationsEmpty}
            </p>
          )}
        </section>
      </div>
    </section>
  );
}
