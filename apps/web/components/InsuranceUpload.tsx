"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import type { DocumentExtractResponse } from "@/lib/types";

export function InsuranceUpload() {
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const [insuranceQuery, setInsuranceQuery] = useState(
    initialFlow.insuranceQuery ?? "USC Aetna student PPO"
  );
  const [uploadedText, setUploadedText] = useState("");
  const [uploadedDocument, setUploadedDocument] = useState<DocumentExtractResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsExtracting(true);
    setError("");
    try {
      const extracted = await api.extractDocument({
        file,
        document_type: "insurance_document",
        title: file.name.replace(/\.[^.]+$/, ""),
      });
      setUploadedDocument(extracted);
      setUploadedText(extracted.extracted_text.slice(0, 6000));
      if (!insuranceQuery || insuranceQuery === "USC Aetna student PPO") {
        setInsuranceQuery(extracted.extracted_text.slice(0, 160));
      }
    } catch (uploadError) {
      setUploadedDocument(null);
      setUploadedText("");
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Unable to read that insurance file right now.",
      );
    } finally {
      setIsExtracting(false);
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
        insurancePlanIdOverride: undefined,
        insurancePurchaseUrl: undefined,
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
      insurancePlanIdOverride: undefined,
      insurancePurchaseUrl: undefined,
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
        <span>Upload insurance card, screenshot, PDF, or text file</span>
        <input
          type="file"
          accept=".txt,.md,.json,.csv,.pdf,.png,.jpg,.jpeg,.gif,.webp,image/*,application/pdf,text/plain"
          onChange={handleFileChange}
        />
      </label>

      {isExtracting ? <p className="upload-status-copy">Extracting text from file...</p> : null}

      {uploadedDocument ? (
        <div className="info-box">
          <div className="document-meta-row">
            <span className="meta-pill">{uploadedDocument.extraction_method}</span>
            <span className="meta-pill">{uploadedDocument.source_mime_type}</span>
          </div>
          <strong>Uploaded preview:</strong>
          <p>{uploadedDocument.extracted_preview}...</p>
          {uploadedDocument.warnings.map((warning) => (
            <p className="document-warning-copy" key={warning}>
              {warning}
            </p>
          ))}
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
