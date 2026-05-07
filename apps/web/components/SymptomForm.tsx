"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { LocationPicker } from "@/components/LocationPicker";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type { Location } from "@/lib/types";

const defaultLocation: Location = {
  latitude: 34.0224,
  longitude: -118.2851,
};

const LEGACY_SYMPTOM_EXAMPLE = "I have had a sore throat and fever for three days.";

export function SymptomForm() {
  const { t } = useTranslation();
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const hasSavedLocation = Boolean(initialFlow.location);
  const sanitizedInitialSymptomText =
    initialFlow.symptomText === LEGACY_SYMPTOM_EXAMPLE ? "" : (initialFlow.symptomText ?? "");
  const [symptomText, setSymptomText] = useState(
    sanitizedInitialSymptomText
  );
  const [preferredLanguage, setPreferredLanguage] = useState(
    initialFlow.preferredLanguage ?? "Mandarin"
  );
  const [location, setLocation] = useState<Location>(
    initialFlow.location ?? defaultLocation
  );
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSymptomHint, setShowSymptomHint] = useState(true);

  useEffect(() => {
    if (initialFlow.symptomText === LEGACY_SYMPTOM_EXAMPLE) {
      patchFlowState({ symptomText: undefined });
    }
  }, [initialFlow.symptomText]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const triage = await api.triage({
        symptom_text: symptomText,
        duration_days: 1,
        location,
      });

      patchFlowState({
        symptomText,
        preferredLanguage,
        location,
        triage,
        searchResult: undefined,
        selectedDoctor: undefined,
      });
      router.push("/insurance");
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : t.symptom.error
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">{t.symptom.step}</span>
        <h2>{t.symptom.title}</h2>
        <p>{t.symptom.subtitle}</p>
      </div>

      <label className="field">
        <span>{t.symptom.symptomsLabel}</span>
        <textarea
          value={symptomText}
          onChange={(event) => setSymptomText(event.target.value)}
          onFocus={() => setShowSymptomHint(false)}
          onBlur={() => setShowSymptomHint(!symptomText.trim())}
          rows={6}
          placeholder={showSymptomHint ? t.symptom.symptomsHint : ""}
        />
      </label>

      <div className="form-grid">
        <label className="field">
          <span>{t.symptom.preferredLanguage}</span>
          <select
            value={preferredLanguage}
            onChange={(event) => setPreferredLanguage(event.target.value)}
          >
            <option value="English">{t.symptom.optionEnglish}</option>
            <option value="Mandarin">{t.symptom.optionMandarin}</option>
            <option value="Spanish">{t.symptom.optionSpanish}</option>
            <option value="Korean">{t.symptom.optionKorean}</option>
          </select>
        </label>
      </div>

      <LocationPicker
        autoLocateOnMount={!hasSavedLocation}
        onChange={setLocation}
        value={location}
      />

      {error ? <p className="error-text">{error}</p> : null}

      <div className="form-actions">
        <button className="button button-primary" type="submit" disabled={isLoading}>
          {isLoading ? t.symptom.reviewing : t.symptom.continueButton}
        </button>
      </div>
    </form>
  );
}
