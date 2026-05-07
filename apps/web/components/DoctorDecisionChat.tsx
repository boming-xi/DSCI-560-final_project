"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type {
  DoctorDecisionConversationTurn,
  DoctorProfile,
  DoctorDecisionSharedBrief,
  UiLanguage,
} from "@/lib/types";

type DoctorDecisionChatProps = {
  doctors: DoctorProfile[];
  symptomText?: string;
  preferredLanguage?: string;
  insuranceQuery?: string;
  uiLanguage: UiLanguage;
  onAcceptRecommendation: (doctorId: string) => void;
  onRecommendationChange: (doctorId: string | null) => void;
};

export function DoctorDecisionChat({
  doctors,
  symptomText,
  preferredLanguage,
  insuranceQuery,
  uiLanguage,
  onAcceptRecommendation,
  onRecommendationChange,
}: DoctorDecisionChatProps) {
  const { t } = useTranslation();
  const doctorIdsSignature = useMemo(
    () => doctors.map((doctor) => doctor.id).join("::"),
    [doctors],
  );
  const roleCards = useMemo(
    () => [
      {
        speaker: t.doctorDecision.fitAnalyst,
        summary: t.doctorDecision.fitAnalystSummary,
      },
      {
        speaker: t.doctorDecision.coverageChecker,
        summary: t.doctorDecision.coverageCheckerSummary,
      },
      {
        speaker: t.doctorDecision.decisionGuide,
        summary: t.doctorDecision.decisionGuideSummary,
      },
    ],
    [t],
  );
  const initialFlow = useMemo(() => getFlowState(), []);
  const useStoredConversation =
    initialFlow.doctorDecisionDoctorIdsSignature === doctorIdsSignature;

  const [conversation, setConversation] = useState<DoctorDecisionConversationTurn[]>(
    useStoredConversation ? initialFlow.doctorDecisionConversation ?? [] : [],
  );
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>(
    useStoredConversation ? initialFlow.doctorDecisionSuggestedPrompts ?? [] : [],
  );
  const [recommendedDoctorId, setRecommendedDoctorId] = useState<string>(
    useStoredConversation ? initialFlow.doctorDecisionRecommendedDoctorId ?? "" : "",
  );
  const [recommendedReason, setRecommendedReason] = useState<string>(
    useStoredConversation ? initialFlow.doctorDecisionRecommendedReason ?? "" : "",
  );
  const [sharedBrief, setSharedBrief] = useState<DoctorDecisionSharedBrief | null>(
    useStoredConversation ? initialFlow.doctorDecisionSharedBrief ?? null : null,
  );
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showPromptHint, setShowPromptHint] = useState(true);
  const hasBootstrapped = useRef(false);

  function persistDecisionState(next: {
    nextConversation: DoctorDecisionConversationTurn[];
    nextSuggestedPrompts: string[];
    nextRecommendedDoctorId: string;
    nextRecommendedReason: string;
    nextSharedBrief: DoctorDecisionSharedBrief | null;
  }) {
    patchFlowState({
      doctorDecisionConversation: next.nextConversation,
      doctorDecisionSuggestedPrompts: next.nextSuggestedPrompts,
      doctorDecisionRecommendedDoctorId: next.nextRecommendedDoctorId || undefined,
      doctorDecisionRecommendedReason: next.nextRecommendedReason || undefined,
      doctorDecisionSharedBrief: next.nextSharedBrief ?? undefined,
      doctorDecisionDoctorIdsSignature: doctorIdsSignature,
    });
  }

  async function requestDecisionAdvice(input: {
    nextMessage: string;
    visibleUserTurn?: DoctorDecisionConversationTurn;
  }) {
    setIsSending(true);
    setError("");

    try {
      const baseConversation = input.visibleUserTurn
        ? [...conversation, input.visibleUserTurn]
        : conversation;
      if (input.visibleUserTurn) {
        setConversation(baseConversation);
      }

      const response = await api.sendDoctorDecisionMessage({
        message: input.nextMessage,
        conversation: baseConversation,
        doctors,
        symptom_text: symptomText,
        insurance_query: insuranceQuery,
        preferred_language: preferredLanguage,
        ui_language: uiLanguage,
      });

      const assistantTurns: DoctorDecisionConversationTurn[] = response.group_messages.map(
        (item) => ({
          role: "assistant",
          speaker: item.speaker,
          content: item.content,
        }),
      );
      const mergedConversation = [...baseConversation, ...assistantTurns];
      const nextRecommendedDoctorId = response.recommended_doctor_id ?? "";
      const nextRecommendedReason = response.recommended_reason ?? "";
      const nextSharedBrief = response.shared_brief ?? null;

      setConversation(mergedConversation);
      setSuggestedPrompts([]);
      setRecommendedDoctorId(nextRecommendedDoctorId);
      setRecommendedReason(nextRecommendedReason);
      setSharedBrief(nextSharedBrief);
      onRecommendationChange(nextRecommendedDoctorId || null);

      persistDecisionState({
        nextConversation: mergedConversation,
        nextSuggestedPrompts: [],
        nextRecommendedDoctorId,
        nextRecommendedReason,
        nextSharedBrief,
      });
    } catch (requestError) {
      if (input.visibleUserTurn) {
        setConversation(conversation);
      }
      setError(
        requestError instanceof Error
          ? requestError.message
          : t.doctorDecision.error,
      );
    } finally {
      setIsSending(false);
    }
  }

  useEffect(() => {
    if (!doctorIdsSignature) {
      return;
    }

    if (initialFlow.doctorDecisionDoctorIdsSignature !== doctorIdsSignature) {
      hasBootstrapped.current = false;
      setConversation([]);
      setSuggestedPrompts([]);
      setRecommendedDoctorId("");
      setRecommendedReason("");
      setSharedBrief(null);
      onRecommendationChange(null);
      patchFlowState({
        doctorDecisionConversation: undefined,
        doctorDecisionSuggestedPrompts: undefined,
        doctorDecisionRecommendedDoctorId: undefined,
        doctorDecisionRecommendedReason: undefined,
        doctorDecisionSharedBrief: undefined,
        doctorDecisionDoctorIdsSignature: doctorIdsSignature,
      });
    }
  }, [doctorIdsSignature, initialFlow.doctorDecisionDoctorIdsSignature]);

  useEffect(() => {
    if (!doctors.length || conversation.length || hasBootstrapped.current) {
      return;
    }

    hasBootstrapped.current = true;
    void requestDecisionAdvice({
      nextMessage: t.doctorDecision.defaultQuestion,
    });
  }, [conversation.length, doctors.length, t.doctorDecision.defaultQuestion]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }

    const nextUserTurn: DoctorDecisionConversationTurn = {
      role: "user",
      speaker: t.doctorDecision.userSpeaker,
      content: message.trim(),
    };
    const nextMessage = nextUserTurn.content;
    setMessage("");
    await requestDecisionAdvice({
      nextMessage,
      visibleUserTurn: nextUserTurn,
    });
  }

  return (
    <section className="panel doctor-decision-panel">
      <div className="panel-heading">
        <span className="eyebrow">{t.doctorDecision.finalChoiceRoom}</span>
        <h2>{t.doctorDecision.title}</h2>
        <p>{t.doctorDecision.subtitle}</p>
      </div>

      <div className="doctor-decision-role-grid">
        {roleCards.map((role) => (
          <article className="doctor-role-card" key={role.speaker}>
            <span className={`doctor-role-pill role-${role.speaker.toLowerCase().replace(/\s+/g, "-")}`}>
              {role.speaker}
            </span>
            <p>{role.summary}</p>
          </article>
        ))}
      </div>

      {sharedBrief ? (
        <article className="doctor-decision-brief">
          <div className="doctor-decision-brief-header">
              <div>
              <span className="eyebrow">{t.doctorDecision.sharedCaseFile}</span>
              <h3>{t.doctorDecision.sharedTitle}</h3>
            </div>
            <span className="meta-pill">{t.doctorDecision.sharedConfirmed}</span>
          </div>

          <p className="doctor-decision-brief-summary">{sharedBrief.case_summary}</p>

          <div className="doctor-decision-brief-grid">
            <div>
              <h4>{t.doctorDecision.patientGoal}</h4>
              <p>{sharedBrief.patient_goal}</p>
            </div>
            <div>
              <h4>{t.doctorDecision.priorityLens}</h4>
              <div className="badge-row compact-badge-row">
                {sharedBrief.priority_labels.map((label) => (
                  <span className="badge" key={label}>
                    {label}
                  </span>
                ))}
              </div>
            </div>
            {sharedBrief.shortlist_names.length ? (
              <div>
                <h4>{t.doctorDecision.shortlistInDiscussion}</h4>
                <p>{sharedBrief.shortlist_names.join(", ")}</p>
              </div>
            ) : null}
            {sharedBrief.coverage_watchout ? (
              <div>
                <h4>{t.doctorDecision.coverageWatchout}</h4>
                <p>{sharedBrief.coverage_watchout}</p>
              </div>
            ) : null}
          </div>
        </article>
      ) : null}

      {recommendedDoctorId ? (
        <div className="info-box doctor-decision-summary">
          <strong>{t.doctorDecision.currentRecommendation}</strong>
          <p>{recommendedReason}</p>
          <button
            className="button button-primary"
            onClick={() => onAcceptRecommendation(recommendedDoctorId)}
            type="button"
          >
            {t.doctorDecision.bookRecommendedDoctor}
          </button>
        </div>
      ) : null}

      <div className="conversation doctor-decision-conversation">
        {conversation.map((turn, index) => (
          <article
            className={`chat-bubble ${turn.role === "assistant" ? "assistant" : "user"} ${
              turn.role === "assistant"
                ? `doctor-speaker-bubble doctor-speaker-${turn.speaker.toLowerCase().replace(/\s+/g, "-")}`
                : ""
            }`}
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
          onFocus={() => setShowPromptHint(false)}
          onBlur={() => setShowPromptHint(!message.trim())}
          placeholder={showPromptHint ? t.doctorDecision.promptHint : ""}
        />
        <button className="button button-primary" disabled={isSending} type="submit">
          {isSending ? t.doctorDecision.comparing : t.doctorDecision.askDecisionGroup}
        </button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
