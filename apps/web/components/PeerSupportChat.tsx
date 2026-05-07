"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type { CommunityRoomResponse } from "@/lib/types";

function guessRegion() {
  return "Los Angeles";
}

function formatRelativeTime(value: string, locale: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function PeerSupportChat() {
  const { t, lang } = useTranslation();
  const locale =
    lang === "Mandarin" ? "zh-CN" : lang === "Spanish" ? "es-ES" : "en-US";
  const initialFlow = useMemo(() => getFlowState(), []);
  const [intakeText, setIntakeText] = useState(
    initialFlow.communityIntakeText ?? initialFlow.symptomText ?? "",
  );
  const [roomState, setRoomState] = useState<CommunityRoomResponse | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isMatching, setIsMatching] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const hasBootstrapped = useRef(false);

  async function loadExistingRoom(roomId: string) {
    const response = await api.getCommunityRoom(roomId, { ui_language: lang });
    setRoomState(response);
  }

  async function matchRoom(nextText?: string) {
    const flow = getFlowState();
    const symptomText = (nextText ?? intakeText).trim();
    if (!symptomText) {
      setError(t.community.roomFallback);
      return;
    }

    setIsMatching(true);
    setError("");
    try {
      const response = await api.matchCommunityRoom({
        symptom_text: symptomText,
        care_path: flow.triage?.care_type,
        urgency_band: flow.triage?.urgency_level,
        preferred_language: flow.preferredLanguage ?? lang,
        region: guessRegion(),
        ui_language: lang,
      });
      setRoomState(response);
      patchFlowState({
        communityRoomId: response.room.id,
        communityIntakeText: symptomText,
      });
    } catch (roomError) {
      setError(roomError instanceof Error ? roomError.message : t.community.roomFallback);
    } finally {
      setIsMatching(false);
    }
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!roomState?.room.id || !message.trim()) {
      return;
    }

    setIsSending(true);
    setError("");
    try {
      const response = await api.sendCommunityMessage(roomState.room.id, {
        content: message.trim(),
        ui_language: lang,
      });
      setRoomState(response);
      setMessage("");
    } catch (messageError) {
      setError(messageError instanceof Error ? messageError.message : t.community.roomFallback);
    } finally {
      setIsSending(false);
    }
  }

  useEffect(() => {
    if (hasBootstrapped.current) {
      return;
    }
    hasBootstrapped.current = true;

    const flow = getFlowState();
    if (flow.communityRoomId) {
      void loadExistingRoom(flow.communityRoomId).catch(() => undefined);
      return;
    }
    if (flow.symptomText?.trim()) {
      void matchRoom(flow.symptomText);
    }
  }, []);

  useEffect(() => {
    if (!roomState?.room.id) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadExistingRoom(roomState.room.id).catch(() => undefined);
    }, 8000);
    return () => window.clearInterval(intervalId);
  }, [lang, roomState?.room.id]);

  return (
    <main className="page-shell">
      <section className="results-header panel">
        <span className="eyebrow">{t.community.step}</span>
        <h1>{t.community.title}</h1>
        <p>{t.community.subtitle}</p>
      </section>

      <section className="panel community-intake-panel">
        <div className="panel-heading">
          <span className="eyebrow">{t.community.intakeTitle}</span>
          <h2>{t.community.intakeSubtitle}</h2>
        </div>

        <form
          className="chat-form"
          onSubmit={(event) => {
            event.preventDefault();
            void matchRoom();
          }}
        >
          <label className="field">
            <span>{t.community.symptomLabel}</span>
            <textarea
              onChange={(event) => setIntakeText(event.target.value)}
              placeholder={t.community.symptomHint}
              rows={4}
              value={intakeText}
            />
          </label>
          <div className="form-actions">
            <button
              className="button button-secondary"
              onClick={() => {
                const flow = getFlowState();
                if (flow.symptomText) {
                  setIntakeText(flow.symptomText);
                }
              }}
              type="button"
            >
              {t.community.useCurrentContext}
            </button>
            <button className="button button-primary" disabled={isMatching} type="submit">
              {isMatching ? t.community.matchingRoom : t.community.joinRoom}
            </button>
          </div>
        </form>
      </section>

      {error ? <div className="panel error-panel">{error}</div> : null}

      {roomState ? (
        <section className="community-layout">
          <article className="panel community-room-panel">
            <div className="panel-heading">
              <span className="eyebrow">{t.community.roomTitle}</span>
              <h2>{roomState.room.title}</h2>
              <p>{roomState.entry_prompt}</p>
            </div>

            <div className="badge-row compact-badge-row">
              <span className="badge">{roomState.room.care_path}</span>
              <span className="badge">{roomState.room.urgency_band}</span>
              <span className="badge">{roomState.room.language}</span>
              <span className="badge">{roomState.room.region}</span>
            </div>

            <div className="conversation community-conversation">
              {roomState.messages.map((turn) => (
                <article
                  className={`chat-bubble ${turn.is_current_user ? "user" : "assistant"}`}
                  key={turn.id}
                >
                  <strong>{turn.display_name}</strong>
                  <ChatMessageContent
                    content={turn.content}
                    role={turn.is_current_user ? "user" : "assistant"}
                  />
                  <p className="subtle-copy">{formatRelativeTime(turn.created_at, locale)}</p>
                </article>
              ))}
            </div>

            {roomState.messages.length <= 1 ? (
              <div className="notice-box">{t.community.noMessages}</div>
            ) : null}

            <form className="chat-form" onSubmit={handleSendMessage}>
              <label className="field">
                <span>{t.community.messageLabel}</span>
                <textarea
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder={t.community.messagePlaceholder}
                  rows={4}
                  value={message}
                />
              </label>
              <div className="form-actions">
                <button
                  className="button button-secondary"
                  onClick={() => void loadExistingRoom(roomState.room.id)}
                  type="button"
                >
                  {t.community.refreshRoom}
                </button>
                <button className="button button-primary" disabled={isSending} type="submit">
                  {isSending ? t.community.sendingMessage : t.community.sendMessage}
                </button>
              </div>
            </form>
          </article>

          <aside className="panel community-sidebar">
            <div className="community-meta-stack">
              <div className="community-meta-card">
                <span className="eyebrow">{t.community.roomMatch}</span>
                <p>{roomState.matching_summary}</p>
              </div>

              <div className="community-meta-card">
                <span className="eyebrow">{t.community.yourAlias}</span>
                <h3>{roomState.your_alias}</h3>
                <div className="badge-row compact-badge-row">
                  <span className="badge">
                    {t.community.roomMembers.replace("{count}", String(roomState.room.member_count))}
                  </span>
                  <span className="badge">
                    {t.community.roomMessages.replace("{count}", String(roomState.room.message_count))}
                  </span>
                </div>
              </div>

              <div className="community-meta-card">
                <span className="eyebrow">{t.community.safetyTitle}</span>
                <p>{roomState.safety_notice}</p>
                <p>{roomState.moderation_notice}</p>
              </div>

              <div className="community-meta-card">
                <span className="eyebrow">{t.community.starterTopics}</span>
                <p>{t.community.sharePrompt}</p>
                <ul className="detail-list">
                  {roomState.starter_topics.map((topic) => (
                    <li key={topic}>{topic}</li>
                  ))}
                </ul>
              </div>
            </div>
          </aside>
        </section>
      ) : null}
    </main>
  );
}
