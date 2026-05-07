"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useTranslation } from "@/lib/LanguageProvider";
import type { DocumentExtractResponse, InsuranceSummary } from "@/lib/types";

const LEGACY_INSURANCE_EXAMPLE = "USC Aetna student PPO";

export function InsuranceUpload() {
  const { t } = useTranslation();
  const router = useRouter();
  const initialFlow = useMemo(() => getFlowState(), []);
  const hasExistingInsuranceFlow = initialFlow.insuranceEntryMode === "has_insurance";
  const sanitizedInitialInsuranceQuery =
    hasExistingInsuranceFlow && initialFlow.insuranceQuery === LEGACY_INSURANCE_EXAMPLE
      ? ""
      : hasExistingInsuranceFlow
      ? (initialFlow.insuranceQuery ?? "")
      : "";
  const [insuranceQuery, setInsuranceQuery] = useState(
    sanitizedInitialInsuranceQuery
  );
  const [uploadedText, setUploadedText] = useState("");
  const [uploadedDocument, setUploadedDocument] = useState<DocumentExtractResponse | null>(null);
  const [reviewedSummary, setReviewedSummary] = useState<InsuranceSummary | null>(
    hasExistingInsuranceFlow ? initialFlow.insuranceSummary ?? null : null,
  );
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
    setReviewedSummary(null);
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
          : t.insurance.uploadError,
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
      setReviewedSummary(insuranceSummary);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : t.insurance.reviewError
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

  function continueToDoctors() {
    router.push("/doctors");
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">{t.insurance.uploadStep}</span>
        <h2>{t.insurance.uploadTitle}</h2>
        <p>{t.insurance.uploadSubtitle}</p>
      </div>

      <label className="field">
        <span>{t.insurance.planTextLabel}</span>
        <textarea
          value={insuranceQuery}
          onChange={(event) => {
            setInsuranceQuery(event.target.value);
            setReviewedSummary(null);
          }}
          onFocus={() => setShowQueryHint(false)}
          onBlur={() => setShowQueryHint(!insuranceQuery.trim())}
          rows={5}
          placeholder={showQueryHint ? t.insurance.planTextHint : ""}
        />
      </label>

      <label className="field">
        <span>{t.insurance.uploadLabel}</span>
        <input
          type="file"
          accept=".txt,.md,.json,.csv,.pdf,.png,.jpg,.jpeg,.gif,.webp,image/*,application/pdf,text/plain"
          onChange={handleFileChange}
        />
      </label>

      {isExtracting ? <p className="upload-status-copy">{t.insurance.readingDocument}</p> : null}

      {uploadedDocument ? (
        <div className="info-box">
          <div className="document-meta-row">
            <span className="meta-pill">{uploadedDocument.extraction_method}</span>
            <span className="meta-pill">{uploadedDocument.source_mime_type}</span>
          </div>
          <strong>{t.insurance.uploadedPreview}</strong>
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
          {isLoading ? t.insurance.reviewingPlan : t.insurance.reviewPlan}
        </button>
        <button className="button button-secondary" type="button" onClick={skipInsurance}>
          {t.insurance.continueWithoutVerification}
        </button>
      </div>

      {reviewedSummary ? (
        <section className="panel insurance-plan-review">
          <div className="panel-heading">
            <span className="eyebrow">{t.insurance.planReviewReady}</span>
            <h3>
              {reviewedSummary.matched
                ? `${reviewedSummary.provider} ${reviewedSummary.plan_name}`
                : t.insurance.coverageCaptured}
            </h3>
            <p>{t.insurance.planReviewTitle}</p>
          </div>

          <div className="insurance-plan-review-grid">
            <article className="insurance-plan-review-item">
              <strong>{t.insurance.planStatus}</strong>
              <p>
                {reviewedSummary.matched
                  ? t.insurance.planStatusMatched
                  : t.insurance.planStatusPartial}
              </p>
            </article>
            <article className="insurance-plan-review-item">
              <strong>{t.insurance.mostImportantNote}</strong>
              <p>
                {reviewedSummary.notes[0] ??
                  t.insurance.fallbackPlanNote}
              </p>
            </article>
          </div>

          <div className="form-actions">
            <button className="button button-primary" onClick={continueToDoctors} type="button">
              {t.insurance.continueToDoctors}
            </button>
          </div>
        </section>
      ) : null}
    </form>
  );
}
