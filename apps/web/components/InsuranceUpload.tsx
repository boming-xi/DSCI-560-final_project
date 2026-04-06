"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";

export function InsuranceUpload() {
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const [insuranceQuery, setInsuranceQuery] = useState(
    initialFlow.insuranceQuery ?? "USC Aetna student PPO"
  );
  const [uploadedText, setUploadedText] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const text = await file.text();
    setUploadedText(text.slice(0, 3000));
    if (!insuranceQuery) {
      setInsuranceQuery(text.slice(0, 120));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const insuranceSummary = await api.parseInsurance({
        insurance_query: insuranceQuery,
        uploaded_text: uploadedText || undefined,
      });

      patchFlowState({
        insuranceQuery,
        insuranceSummary,
        searchResult: undefined,
        selectedDoctor: undefined,
        booking: undefined,
      });
      router.push("/doctors");
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to parse insurance right now."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function skipInsurance() {
    patchFlowState({
      insuranceQuery: "",
      insuranceSummary: undefined,
      searchResult: undefined,
      selectedDoctor: undefined,
      booking: undefined,
    });
    router.push("/doctors");
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">Step 2</span>
        <h2>Add insurance details</h2>
        <p>
          Paste plan text, upload a text extract from an insurance card, or skip
          this step and browse with softer matching.
        </p>
      </div>

      <label className="field">
        <span>Insurance plan text</span>
        <textarea
          value={insuranceQuery}
          onChange={(event) => setInsuranceQuery(event.target.value)}
          rows={5}
          placeholder="Aetna USC Student Health PPO"
        />
      </label>

      <label className="field">
        <span>Upload text file from insurance card or policy</span>
        <input type="file" accept=".txt,.md,.json" onChange={handleFileChange} />
      </label>

      {uploadedText ? (
        <div className="info-box">
          <strong>Uploaded preview:</strong>
          <p>{uploadedText.slice(0, 160)}...</p>
        </div>
      ) : null}

      {error ? <p className="error-text">{error}</p> : null}

      <div className="form-actions">
        <button className="button button-primary" type="submit" disabled={isLoading}>
          {isLoading ? "Matching plan..." : "Find doctors"}
        </button>
        <button className="button button-secondary" type="button" onClick={skipInsurance}>
          Continue without insurance
        </button>
      </div>
    </form>
  );
}

