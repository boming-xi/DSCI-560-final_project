"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { patchFlowState, getFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type { UiLanguage } from "@/lib/types";

function guessRegion() {
  return "Los Angeles";
}

export function CreateSupportRoomForm() {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const flow = useMemo(() => getFlowState(), []);

  const [customRoomTitle, setCustomRoomTitle] = useState("");
  const [customRoomFocus, setCustomRoomFocus] = useState("");
  const [customRoomLanguage, setCustomRoomLanguage] = useState<UiLanguage>(lang);
  const [customRoomCarePath, setCustomRoomCarePath] = useState(
    flow.triage?.care_type ?? "General care",
  );
  const [customRoomUrgency, setCustomRoomUrgency] = useState<
    "self-care" | "routine" | "soon" | "urgent" | "emergency"
  >(flow.triage?.urgency_level ?? "routine");
  const [error, setError] = useState("");
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);

  async function handleCreateRoom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentFlow = getFlowState();
    const title = customRoomTitle.trim();
    const focus = customRoomFocus.trim();
    if (!title || !focus) {
      setError(t.community.createRoomNeedsMoreDetail);
      return;
    }

    setIsCreatingRoom(true);
    setError("");
    try {
      const response = await api.createCommunityRoom({
        title,
        focus,
        symptom_text: currentFlow.communityIntakeText?.trim() || currentFlow.symptomText || undefined,
        care_path: customRoomCarePath,
        urgency_band: customRoomUrgency,
        preferred_language: customRoomLanguage,
        region: guessRegion(),
        ui_language: lang,
      });
      patchFlowState({
        communityRoomId: response.room.id,
        communityIntakeText: currentFlow.communityIntakeText?.trim() || currentFlow.symptomText || undefined,
      });
      router.push(`/group-chat/${encodeURIComponent(response.room.id)}`);
    } catch (createError) {
      setError(
        createError instanceof Error
          ? createError.message
          : t.community.roomFallback,
      );
    } finally {
      setIsCreatingRoom(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="results-header panel">
        <span className="eyebrow">{t.community.createRoomTitle}</span>
        <h1>{t.community.createRoomStandaloneTitle}</h1>
        <p>{t.community.createRoomSubtitle}</p>
      </section>

      <section className="panel community-create-page">
        <div className="panel-heading">
          <span className="eyebrow">{t.community.createRoomTitle}</span>
          <h2>{t.community.createRoomStandaloneSubtitle}</h2>
        </div>

        <form className="chat-form" onSubmit={handleCreateRoom}>
          <div className="community-filter-grid">
            <label className="field">
              <span>{t.community.createRoomNameLabel}</span>
              <input
                onChange={(event) => setCustomRoomTitle(event.target.value)}
                placeholder={t.community.createRoomNameHint}
                type="text"
                value={customRoomTitle}
              />
            </label>
            <label className="field">
              <span>{t.community.createRoomLanguageLabel}</span>
              <select
                onChange={(event) =>
                  setCustomRoomLanguage(event.target.value as UiLanguage)
                }
                value={customRoomLanguage}
              >
                <option value="English">English</option>
                <option value="Mandarin">中文</option>
                <option value="Spanish">Español</option>
              </select>
            </label>
            <label className="field">
              <span>{t.community.createRoomCarePathLabel}</span>
              <select
                onChange={(event) => setCustomRoomCarePath(event.target.value)}
                value={customRoomCarePath}
              >
                <option value="General care">{t.community.createRoomCarePathGeneral}</option>
                <option value="Primary care">{t.community.createRoomCarePathPrimary}</option>
                <option value="Urgent care">{t.community.createRoomCarePathUrgent}</option>
                <option value="Specialist follow-up">{t.community.createRoomCarePathSpecialist}</option>
              </select>
            </label>
          </div>

          <label className="field">
            <span>{t.community.createRoomFocusLabel}</span>
            <textarea
              onChange={(event) => setCustomRoomFocus(event.target.value)}
              placeholder={t.community.createRoomFocusHint}
              rows={5}
              value={customRoomFocus}
            />
          </label>

          <div className="community-filter-grid community-create-grid-tight">
            <label className="field">
              <span>{t.community.createRoomUrgencyLabel}</span>
              <select
                onChange={(event) =>
                  setCustomRoomUrgency(
                    event.target.value as
                      | "self-care"
                      | "routine"
                      | "soon"
                      | "urgent"
                      | "emergency",
                  )
                }
                value={customRoomUrgency}
              >
                <option value="routine">{t.community.createRoomUrgencyRoutine}</option>
                <option value="soon">{t.community.createRoomUrgencySoon}</option>
                <option value="urgent">{t.community.createRoomUrgencyUrgent}</option>
              </select>
            </label>
            <div className="community-create-note">
              <span className="eyebrow">{t.community.contextSummaryTitle}</span>
              <p>{t.community.createRoomContextNote}</p>
            </div>
          </div>

          {error ? <div className="panel error-panel">{error}</div> : null}

          <div className="form-actions">
            <button
              className="button button-secondary"
              onClick={() => router.push("/group-chat")}
              type="button"
            >
              {t.community.backToRooms}
            </button>
            <button
              className="button button-primary"
              disabled={isCreatingRoom}
              type="submit"
            >
              {isCreatingRoom
                ? t.community.creatingRoom
                : t.community.createRoomButton}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
