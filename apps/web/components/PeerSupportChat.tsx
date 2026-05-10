"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type {
  CommunityRoomCatalogResponse,
  CommunityRoomResponse,
  CommunityRoomSummary,
} from "@/lib/types";

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

type ActivityState = "active_now" | "recently_active" | "quiet";

function getActivityState(value: string): ActivityState {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "quiet";
  }
  const diffMs = Date.now() - date.getTime();
  if (diffMs <= 60 * 60 * 1000) {
    return "active_now";
  }
  if (diffMs <= 24 * 60 * 60 * 1000) {
    return "recently_active";
  }
  return "quiet";
}

type PeerSupportChatProps = {
  initialRoomId?: string;
  roomOnly?: boolean;
};

export function PeerSupportChat({
  initialRoomId,
  roomOnly = false,
}: PeerSupportChatProps = {}) {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const locale =
    lang === "Mandarin" ? "zh-CN" : lang === "Spanish" ? "es-ES" : "en-US";
  const initialFlow = useMemo(() => getFlowState(), []);
  const [intakeText, setIntakeText] = useState(
    initialFlow.communityIntakeText ?? initialFlow.symptomText ?? "",
  );
  const [catalogState, setCatalogState] =
    useState<CommunityRoomCatalogResponse | null>(null);
  const [roomState, setRoomState] = useState<CommunityRoomResponse | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isMatching, setIsMatching] = useState(false);
  const [isJoiningRoomId, setIsJoiningRoomId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [hasMatched, setHasMatched] = useState(false);
  const [carePathFilter, setCarePathFilter] = useState("all");
  const [languageFilter, setLanguageFilter] = useState("all");
  const [activityFilter, setActivityFilter] = useState<ActivityState | "all">(
    "all",
  );
  const hasBootstrapped = useRef(false);
  const hasAppliedLanguageRefresh = useRef(false);

  async function loadExistingRoom(roomId: string) {
    try {
      const response = await api.getCommunityRoom(roomId, { ui_language: lang });
      setRoomState(response);
    } catch {
      setRoomState(null);
      patchFlowState({ communityRoomId: undefined });
      if (roomOnly) {
        setError(t.community.roomFallback);
      }
    }
  }

  async function discoverRooms(
    nextText?: string,
    options?: { markAsMatched?: boolean },
  ) {
    const flow = getFlowState();
    const symptomText = (nextText ?? intakeText).trim();

    setIsMatching(true);
    setError("");
    try {
      const response = await api.discoverCommunityRooms({
        symptom_text: symptomText || undefined,
        care_path: flow.triage?.care_type,
        urgency_band: flow.triage?.urgency_level,
        preferred_language: flow.preferredLanguage ?? lang,
        region: guessRegion(),
        ui_language: lang,
      });
      setCatalogState(response);
      if (options?.markAsMatched) {
        setHasMatched(Boolean(symptomText));
      }
      patchFlowState({ communityIntakeText: symptomText || undefined });
    } catch (roomError) {
      setError(
        roomError instanceof Error ? roomError.message : t.community.roomFallback,
      );
    } finally {
      setIsMatching(false);
    }
  }

  async function joinRoom(room: CommunityRoomSummary) {
    const flow = getFlowState();
    setIsJoiningRoomId(room.id);
    setError("");
    try {
      const response = await api.joinCommunityRoom(room.id, {
        symptom_text: intakeText.trim() || flow.symptomText || undefined,
        care_path: flow.triage?.care_type,
        urgency_band: flow.triage?.urgency_level,
        preferred_language: flow.preferredLanguage ?? lang,
        region: guessRegion(),
        ui_language: lang,
      });
      patchFlowState({
        communityRoomId: response.room.id,
        communityIntakeText: intakeText.trim() || undefined,
      });
      router.push(`/group-chat/${encodeURIComponent(response.room.id)}`);
    } catch (joinError) {
      setError(
        joinError instanceof Error ? joinError.message : t.community.roomFallback,
      );
    } finally {
      setIsJoiningRoomId(null);
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
      setError(
        messageError instanceof Error
          ? messageError.message
          : t.community.roomFallback,
      );
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
    if (roomOnly && initialRoomId) {
      void loadExistingRoom(initialRoomId).catch(() => undefined);
      return;
    }
    if (!roomOnly) {
      void discoverRooms(flow.communityIntakeText ?? flow.symptomText ?? "");
    }
  }, [initialRoomId, roomOnly]);

  useEffect(() => {
    if (!roomState?.room.id) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadExistingRoom(roomState.room.id).catch(() => undefined);
    }, 8000);
    return () => window.clearInterval(intervalId);
  }, [roomState?.room.id]);

  useEffect(() => {
    if (!hasBootstrapped.current || !hasAppliedLanguageRefresh.current) {
      hasAppliedLanguageRefresh.current = true;
      return;
    }
    if (roomOnly && initialRoomId) {
      void loadExistingRoom(initialRoomId).catch(() => undefined);
      return;
    }
    const flow = getFlowState();
    void discoverRooms(flow.communityIntakeText ?? intakeText);
  }, [initialRoomId, lang, roomOnly]);

  const roomPool = useMemo(() => {
    if (!catalogState) {
      return [];
    }
    const seen = new Set<string>();
    return [...catalogState.recommended_rooms, ...catalogState.browse_rooms].filter(
      (room) => {
        if (seen.has(room.id)) {
          return false;
        }
        seen.add(room.id);
        return true;
      },
    );
  }, [catalogState]);

  const carePathOptions = useMemo(
    () => Array.from(new Set(roomPool.map((room) => room.care_path))),
    [roomPool],
  );

  const languageOptions = useMemo(
    () => Array.from(new Set(roomPool.map((room) => room.language))),
    [roomPool],
  );

  function roomMatchesFilters(room: CommunityRoomSummary) {
    if (carePathFilter !== "all" && room.care_path !== carePathFilter) {
      return false;
    }
    if (languageFilter !== "all" && room.language !== languageFilter) {
      return false;
    }
    if (
      activityFilter !== "all" &&
      getActivityState(room.latest_activity_at) !== activityFilter
    ) {
      return false;
    }
    return true;
  }

  const filteredRecommendedRooms = useMemo(
    () => (catalogState?.recommended_rooms ?? []).filter(roomMatchesFilters),
    [activityFilter, carePathFilter, catalogState, languageFilter],
  );

  const filteredBrowseRooms = useMemo(
    () => (catalogState?.browse_rooms ?? []).filter(roomMatchesFilters),
    [activityFilter, carePathFilter, catalogState, languageFilter],
  );

  function activityLabel(state: ActivityState) {
    if (state === "active_now") {
      return t.community.activeNow;
    }
    if (state === "recently_active") {
      return t.community.recentlyActive;
    }
    return t.community.quietRoom;
  }

  function seedMessage(topic: string) {
    setMessage((current) =>
      current.trim() ? `${current.trim()}\n\n${topic}` : topic,
    );
  }

  return (
    <main className="page-shell">
      {roomOnly ? (
        roomState ? (
          <section className="panel community-room-page-header">
            <button
              className="button button-secondary"
              onClick={() => router.push("/group-chat")}
              type="button"
            >
              {t.community.backToRooms}
            </button>
            <div className="community-room-page-copy">
              <span className="eyebrow">{t.community.roomTitle}</span>
              <h1>{roomState.room.title}</h1>
              <p>{roomState.entry_prompt}</p>
            </div>
          </section>
        ) : (
          <section className="panel community-room-page-header">
            <button
              className="button button-secondary"
              onClick={() => router.push("/group-chat")}
              type="button"
            >
              {t.community.backToRooms}
            </button>
          </section>
        )
      ) : (
        <section className="results-header panel">
          <span className="eyebrow">{t.community.step}</span>
          <h1>{t.community.title}</h1>
          <p>{t.community.subtitle}</p>
        </section>
      )}

      {!roomOnly ? (
        <div className="community-top-grid">
          <section className="panel community-intake-panel">
            <div className="panel-heading">
              <span className="eyebrow">{t.community.intakeTitle}</span>
              <h2>{t.community.intakeSubtitle}</h2>
            </div>

            <form
              className="chat-form"
              onSubmit={(event) => {
                event.preventDefault();
                const flow = getFlowState();
                const nextText = intakeText.trim() || flow.symptomText?.trim() || "";
                if (!nextText) {
                  setError(t.community.addContextToMatch);
                  setHasMatched(false);
                  return;
                }
                void discoverRooms(nextText, { markAsMatched: true });
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
                <button
                  className="button button-secondary"
                  onClick={() => router.push("/group-chat/create")}
                  type="button"
                >
                  {t.community.goToCreateRoom}
                </button>
                <button
                  className="button button-primary"
                  disabled={isMatching}
                  type="submit"
                >
                  {isMatching ? t.community.matchingRoom : t.community.joinRoom}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}

      {error ? <div className="panel error-panel">{error}</div> : null}

      {!roomOnly && catalogState ? (
        <section className="community-section-stack">
          <div className="panel community-context-panel">
            <span className="eyebrow">{t.community.contextSummaryTitle}</span>
            <p>{catalogState.selected_context_summary}</p>
          </div>

          <section className="panel community-filters-panel">
            <div className="panel-heading">
              <span className="eyebrow">{t.community.roomFiltersTitle}</span>
              <h2>{t.community.roomFiltersSubtitle}</h2>
            </div>
            <div className="community-filter-grid">
              <label className="field">
                <span>{t.community.filterCarePath}</span>
                <select
                  onChange={(event) => setCarePathFilter(event.target.value)}
                  value={carePathFilter}
                >
                  <option value="all">{t.community.allCarePaths}</option>
                  {carePathOptions.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>{t.community.filterLanguage}</span>
                <select
                  onChange={(event) => setLanguageFilter(event.target.value)}
                  value={languageFilter}
                >
                  <option value="all">{t.community.allLanguages}</option>
                  {languageOptions.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>{t.community.filterActivity}</span>
                <select
                  onChange={(event) =>
                    setActivityFilter(event.target.value as ActivityState | "all")
                  }
                  value={activityFilter}
                >
                  <option value="all">{t.community.allActivity}</option>
                  <option value="active_now">{t.community.activeNow}</option>
                  <option value="recently_active">{t.community.recentlyActive}</option>
                  <option value="quiet">{t.community.quietRoom}</option>
                </select>
              </label>
            </div>
          </section>

          {hasMatched ? (
            <section className="panel">
              <div className="panel-heading">
                <span className="eyebrow">{t.community.recommendedRoomsTitle}</span>
                <h2>{t.community.recommendedRoomsSubtitle}</h2>
              </div>
              {filteredRecommendedRooms.length ? (
                <div className="community-room-grid">
                  {filteredRecommendedRooms.map((room, index) => (
                    <article className="community-room-card" key={room.id}>
                      <div className="community-room-card-top">
                        <div>
                          <h3>{room.title}</h3>
                          <div className="badge-row compact-badge-row">
                            {index === 0 ? (
                              <span className="badge">{t.community.bestMatchLabel}</span>
                            ) : null}
                            <span className="badge">{room.care_path}</span>
                            <span className="badge">{room.urgency_band}</span>
                            <span className="badge">{room.language}</span>
                          </div>
                        </div>
                        <button
                          className="button button-primary"
                          disabled={isJoiningRoomId === room.id}
                          onClick={() => void joinRoom(room)}
                          type="button"
                        >
                          {isJoiningRoomId === room.id
                            ? t.community.matchingRoom
                            : t.community.joinThisRoom}
                        </button>
                      </div>

                      <div className="community-room-meta-row">
                        <span
                          className={`community-activity-badge ${getActivityState(
                            room.latest_activity_at,
                          )}`}
                        >
                          {activityLabel(getActivityState(room.latest_activity_at))}
                        </span>
                        <span className="subtle-copy">
                          {t.community.latestActivity.replace(
                            "{time}",
                            formatRelativeTime(room.latest_activity_at, locale),
                          )}
                        </span>
                      </div>

                      <div className="community-room-card-copy">
                        {room.match_reason ? (
                          <div>
                            <strong>{t.community.roomReasonTitle}</strong>
                            <p>{room.match_reason}</p>
                          </div>
                        ) : null}
                        {room.description ? (
                          <div>
                            <strong>{t.community.roomDescriptionTitle}</strong>
                            <p>{room.description}</p>
                          </div>
                        ) : null}
                        {room.preview_topics.length ? (
                          <div>
                            <strong>{t.community.previewTopics}</strong>
                            <div className="badge-row compact-badge-row">
                              {room.preview_topics.map((topic) => (
                                <span className="badge" key={`${room.id}-${topic}`}>
                                  {topic}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : null}
                      </div>

                      <div className="badge-row compact-badge-row">
                        {room.symptom_tags.map((tag) => (
                          <span className="badge" key={`${room.id}-${tag}`}>
                            {tag}
                          </span>
                        ))}
                        <span className="badge">
                          {t.community.roomMembers.replace(
                            "{count}",
                            String(room.member_count),
                          )}
                        </span>
                        <span className="badge">
                          {t.community.roomMessages.replace(
                            "{count}",
                            String(room.message_count),
                          )}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="notice-box">
                  {catalogState.recommended_rooms.length
                    ? t.community.noRoomsAfterFilters
                    : t.community.noRecommendedRooms}
                </div>
              )}
            </section>
          ) : null}

          <section className="panel">
            <div className="panel-heading">
              <span className="eyebrow">
                {hasMatched
                  ? t.community.browseRoomsTitle
                  : t.community.availableRoomsTitle}
              </span>
              <h2>
                {hasMatched
                  ? t.community.browseRoomsSubtitle
                  : t.community.availableRoomsSubtitle}
              </h2>
            </div>
            {filteredBrowseRooms.length ? (
              <div className="community-room-grid">
                {filteredBrowseRooms.map((room) => (
                  <article className="community-room-card" key={room.id}>
                    <div className="community-room-card-top">
                      <div>
                        <h3>{room.title}</h3>
                        <div className="badge-row compact-badge-row">
                          <span className="badge">{room.care_path}</span>
                          <span className="badge">{room.urgency_band}</span>
                          <span className="badge">{room.language}</span>
                        </div>
                      </div>
                      <button
                        className="button button-secondary"
                        disabled={isJoiningRoomId === room.id}
                        onClick={() => void joinRoom(room)}
                        type="button"
                      >
                        {isJoiningRoomId === room.id
                          ? t.community.matchingRoom
                          : t.community.joinThisRoom}
                      </button>
                    </div>

                    <div className="community-room-meta-row">
                      <span
                        className={`community-activity-badge ${getActivityState(
                          room.latest_activity_at,
                        )}`}
                      >
                        {activityLabel(getActivityState(room.latest_activity_at))}
                      </span>
                      <span className="subtle-copy">
                        {t.community.latestActivity.replace(
                          "{time}",
                          formatRelativeTime(room.latest_activity_at, locale),
                        )}
                      </span>
                    </div>

                    <div className="community-room-card-copy">
                      {room.description ? (
                        <div>
                          <strong>{t.community.roomDescriptionTitle}</strong>
                          <p>{room.description}</p>
                        </div>
                      ) : null}
                      {room.preview_topics.length ? (
                        <div>
                          <strong>{t.community.previewTopics}</strong>
                          <div className="badge-row compact-badge-row">
                            {room.preview_topics.map((topic) => (
                              <span className="badge" key={`${room.id}-${topic}`}>
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>

                    <div className="badge-row compact-badge-row">
                      {room.symptom_tags.map((tag) => (
                        <span className="badge" key={`${room.id}-${tag}`}>
                          {tag}
                        </span>
                      ))}
                      <span className="badge">{room.region}</span>
                      <span className="badge">
                        {t.community.roomMembers.replace(
                          "{count}",
                          String(room.member_count),
                        )}
                      </span>
                      <span className="badge">
                        {t.community.roomMessages.replace(
                          "{count}",
                          String(room.message_count),
                        )}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="notice-box">
                {catalogState.browse_rooms.length
                  ? t.community.noRoomsAfterFilters
                  : t.community.noBrowseRooms}
              </div>
            )}
          </section>
        </section>
      ) : null}

      {roomState ? (
        <section className="community-layout" id="current-support-room">
          <article className="panel community-room-panel">
            {roomOnly ? null : (
              <div className="panel-heading">
                <span className="eyebrow">{t.community.roomTitle}</span>
                <h2>{roomState.room.title}</h2>
                <p>{roomState.entry_prompt}</p>
              </div>
            )}

            <div className="badge-row compact-badge-row">
              <span className="badge">{roomState.room.care_path}</span>
              <span className="badge">{roomState.room.urgency_band}</span>
              <span className="badge">{roomState.room.language}</span>
              <span className="badge">{roomState.room.region}</span>
              <span
                className={`community-activity-badge ${getActivityState(
                  roomState.room.latest_activity_at,
                )}`}
              >
                {activityLabel(getActivityState(roomState.room.latest_activity_at))}
              </span>
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
                  <p className="subtle-copy">
                    {formatRelativeTime(turn.created_at, locale)}
                  </p>
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
              <div className="community-message-helpers">
                <span>{t.community.quickStartTitle}</span>
                <div className="badge-row compact-badge-row">
                  {roomState.starter_topics.map((topic) => (
                    <button
                      className="badge badge-button"
                      key={topic}
                      onClick={() => seedMessage(topic)}
                      type="button"
                    >
                      {topic}
                    </button>
                  ))}
                </div>
              </div>
              <div className="form-actions">
                <button
                  className="button button-secondary"
                  onClick={() => void loadExistingRoom(roomState.room.id)}
                  type="button"
                >
                  {t.community.refreshRoom}
                </button>
                <button
                  className="button button-primary"
                  disabled={isSending}
                  type="submit"
                >
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
                    {t.community.roomMembers.replace(
                      "{count}",
                      String(roomState.room.member_count),
                    )}
                  </span>
                  <span className="badge">
                    {t.community.roomMessages.replace(
                      "{count}",
                      String(roomState.room.message_count),
                    )}
                  </span>
                  <span className="badge">
                    {t.community.latestActivity.replace(
                      "{time}",
                      formatRelativeTime(roomState.room.latest_activity_at, locale),
                    )}
                  </span>
                </div>
              </div>

              <div className="community-meta-card">
                <span className="eyebrow">{t.community.previewTopics}</span>
                <div className="badge-row compact-badge-row">
                  {roomState.room.preview_topics.map((topic) => (
                    <span className="badge" key={topic}>
                      {topic}
                    </span>
                  ))}
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
