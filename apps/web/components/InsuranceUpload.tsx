"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import type { DocumentExtractResponse } from "@/lib/types";

const LEGACY_INSURANCE_EXAMPLE = "USC Aetna student PPO";
const INSURANCE_QUERY_HINT =
  "Paste the carrier, plan name, or the key text you see on your insurance card or marketplace plan.";

export function InsuranceUpload() {
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const sanitizedInitialInsuranceQuery =
    initialFlow.insuranceQuery === LEGACY_INSURANCE_EXAMPLE
      ? ""
      : (initialFlow.insuranceQuery ?? "");
  const [insuranceQuery, setInsuranceQuery] = useState(
    sanitizedInitialInsuranceQuery
  );
  const [uploadedText, setUploadedText] = useState("");
  const [uploadedDocument, setUploadedDocument] = useState<DocumentExtractResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [showQueryHint, setShowQueryHint] = useState(true);

  useEffect(() => {
    if (initialFlow.insuranceQuery === LEGACY_INSURANCE_EXAMPLE) {
      patchFlowState({ insuranceQuery: undefined });
    }
  }, [initialFlow.insuranceQuery]);

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
      if (!insuranceQuery || insuranceQuery === LEGACY_INSURANCE_EXAMPLE) {
        setInsuranceQuery(extracted.extracted_text.slice(0, 160));
      }
    } catch (uploadError) {
      setUploadedDocument(null);
      setUploadedText("");
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "We could not read that insurance file just yet.",
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
        insuranceEntryMode: "has_insurance",
        insuranceQuery,
        insuranceSummary,
        insurancePlanIdOverride: undefined,
        insurancePurchaseUrl: undefined,
        insuranceNetworkUrl: undefined,
        searchResult: undefined,
        selectedDoctor: undefined,
      });
      router.push("/doctors");
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "We could not review that plan just yet."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function skipInsurance() {
    patchFlowState({
      insuranceEntryMode: "has_insurance",
      insuranceQuery: "",
      insuranceSummary: undefined,
      insurancePlanIdOverride: undefined,
      insurancePurchaseUrl: undefined,
      insuranceNetworkUrl: undefined,
      searchResult: undefined,
      selectedDoctor: undefined,
    });
    router.push("/doctors");
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">Step 2</span>
        <h2>Use your existing insurance</h2>
        <p>
          Paste plan text or upload an insurance card, screenshot, or PDF. We
          will parse the plan first, then carry it into doctor matching.
        </p>
      </div>

      <label className="field">
        <span>Insurance plan text</span>
        <textarea
          value={insuranceQuery}
          onChange={(event) => setInsuranceQuery(event.target.value)}
          onFocus={() => setShowQueryHint(false)}
          onBlur={() => setShowQueryHint(!insuranceQuery.trim())}
          rows={5}
          placeholder={showQueryHint ? INSURANCE_QUERY_HINT : ""}
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

      {isExtracting ? <p className="upload-status-copy">Reading your insurance document...</p> : null}

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
          {isLoading ? "Reviewing plan details..." : "Match plan and continue"}
        </button>
        <button className="button button-secondary" type="button" onClick={skipInsurance}>
          Continue without plan verification
        </button>
      </div>
    </form>
  );
}
