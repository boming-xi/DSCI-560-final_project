"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { LocationPicker } from "@/components/LocationPicker";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import type { Location } from "@/lib/types";

const defaultLocation: Location = {
  latitude: 34.0224,
  longitude: -118.2851,
};

export function SymptomForm() {
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const hasSavedLocation = Boolean(initialFlow.location);
  const [symptomText, setSymptomText] = useState(
    initialFlow.symptomText ?? "I have had a sore throat and fever for three days."
  );
  const [durationDays, setDurationDays] = useState(initialFlow.durationDays ?? 3);
  const [preferredLanguage, setPreferredLanguage] = useState(
    initialFlow.preferredLanguage ?? "Mandarin"
  );
  const [location, setLocation] = useState<Location>(
    initialFlow.location ?? defaultLocation
  );
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const triage = await api.triage({
        symptom_text: symptomText,
        duration_days: durationDays,
        location,
      });

      patchFlowState({
        symptomText,
        durationDays,
        preferredLanguage,
        location,
        triage,
        searchResult: undefined,
        selectedDoctor: undefined,
        booking: undefined,
      });
      router.push("/insurance");
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to analyze symptoms right now."
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
          rows={6}
          placeholder="I have had a sore throat and fever for three days..."
        />
      </label>

      <div className="form-grid">
        <label className="field">
          <span>Duration (days)</span>
          <input
            type="number"
            min={1}
            value={durationDays}
            onChange={(event) => setDurationDays(Number(event.target.value))}
          />
        </label>
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
          {isLoading ? "Analyzing..." : "Continue to insurance"}
        </button>
      </div>
    </form>
  );
}
