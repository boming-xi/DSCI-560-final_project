"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { LocationPicker } from "@/components/LocationPicker";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import type { Location } from "@/lib/types";

const defaultLocation: Location = {
  latitude: 34.0224,
  longitude: -118.2851,
};

const LEGACY_SYMPTOM_EXAMPLE = "I have had a sore throat and fever for three days.";
const SYMPTOM_HINT =
  "Describe what you're feeling, how it started, and what feels most urgent right now.";

export function SymptomForm() {
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
          : "We could not review those symptoms just yet."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">Step 1</span>
        <h2>Describe what is going on</h2>
        <p>
          We turn symptom text into an urgency band and the most likely care
          starting point.
        </p>
      </div>

      <label className="field">
        <span>Symptoms</span>
        <textarea
          value={symptomText}
          onChange={(event) => setSymptomText(event.target.value)}
          onFocus={() => setShowSymptomHint(false)}
          onBlur={() => setShowSymptomHint(!symptomText.trim())}
          rows={6}
          placeholder={showSymptomHint ? SYMPTOM_HINT : ""}
        />
      </label>

      <div className="form-grid">
        <label className="field">
          <span>Preferred language</span>
          <select
            value={preferredLanguage}
            onChange={(event) => setPreferredLanguage(event.target.value)}
          >
            <option value="English">English</option>
            <option value="Mandarin">Mandarin</option>
            <option value="Spanish">Spanish</option>
            <option value="Korean">Korean</option>
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
          {isLoading ? "Reviewing symptoms..." : "Continue to insurance"}
        </button>
      </div>
    </form>
  );
}
