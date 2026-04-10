"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState, patchFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import type {
  ChatTurn,
  DocumentExplainResponse,
  DocumentExtractResponse,
} from "@/lib/types";

const defaultDocumentText =
  "CBC results: WBC slightly elevated. Mild inflammation noted. Follow up if fever persists.";
const defaultDocumentType = "medical_report";
const defaultFocusQuestion = "What matters most?";

function buildDocumentSnapshot(input: {
  title: string;
  documentType: string;
  documentText: string;
}) {
  return `${input.title.trim()}::${input.documentType.trim()}::${input.documentText.trim()}`;
}

type DocumentDraft = {
  title: string;
  documentType: string;
  documentText: string;
  documentId?: string;
};

export default function ChatPage() {
  const { isCheckingAuth, session } = useProtectedRoute();
  const flow = useMemo(() => getFlowState(), []);
  const [conversation, setConversation] = useState<ChatTurn[]>([
    {
      role: "assistant",
      content:
        "Ask me about symptoms, what kind of doctor to see, or what your insurance might imply.",
    },
  ]);
  const [message, setMessage] = useState("Can you summarize what kind of care I probably need?");
  const [documentText, setDocumentText] = useState(
    flow.documentText ?? defaultDocumentText
  );
  const [documentTitle, setDocumentTitle] = useState(flow.documentTitle ?? "Lab report notes");
  const [documentType, setDocumentType] = useState(flow.documentType ?? defaultDocumentType);
  const [documentId, setDocumentId] = useState(flow.documentId ?? "");
  const [focusQuestion, setFocusQuestion] = useState(
    flow.documentFocusQuestion ?? defaultFocusQuestion,
  );
  const [indexedDocumentSnapshot, setIndexedDocumentSnapshot] = useState(
    flow.documentId
      ? buildDocumentSnapshot({
          title: flow.documentTitle ?? "Lab report notes",
          documentType: flow.documentType ?? defaultDocumentType,
          documentText: flow.documentText ?? "",
        })
      : "",
  );
  const [documentSummary, setDocumentSummary] = useState<DocumentExplainResponse | null>(null);
  const [uploadedDocument, setUploadedDocument] = useState<DocumentExtractResponse | null>(null);
  const [documentError, setDocumentError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [isExtractingDocument, setIsExtractingDocument] = useState(false);

  const trimmedDocumentText = documentText.trim();
  const trimmedFocusQuestion = focusQuestion.trim() || defaultFocusQuestion;
  const currentDocumentSnapshot = buildDocumentSnapshot({
    title: documentTitle,
    documentType,
    documentText,
  });
  const isDocumentDirty = Boolean(documentId) && currentDocumentSnapshot !== indexedDocumentSnapshot;
  const canReuseIndexedDocument = Boolean(documentId) && !isDocumentDirty;

  function persistDocumentFlow(next: {
    documentTitle?: string;
    documentType?: string;
    documentText?: string;
    documentId?: string;
    documentFocusQuestion?: string;
  }) {
    patchFlowState(next);
  }

  async function handleChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }

    const nextConversation: ChatTurn[] = [
      ...conversation,
      { role: "user", content: message },
    ];
    setConversation(nextConversation);
    setMessage("");
    setIsSending(true);

    try {
      const reply = await api.sendChat({
        message,
        conversation: nextConversation,
        symptom_text: flow.symptomText,
        insurance_query: flow.insuranceQuery,
      });

      setConversation((current) => [
        ...current,
        { role: "assistant", content: reply.reply },
      ]);
    } catch (error) {
      setConversation((current) => [
        ...current,
        {
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "Unable to send your message right now.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  async function requestDocumentExplanation(options?: {
    question?: string;
    allowReuse?: boolean;
    draft?: DocumentDraft;
  }) {
    const resolvedQuestion = options?.question?.trim() || trimmedFocusQuestion;
    const resolvedTitle = options?.draft?.title ?? documentTitle;
    const resolvedDocumentType = options?.draft?.documentType ?? documentType;
    const resolvedDocumentText = options?.draft?.documentText ?? documentText;
    const resolvedDocumentId = options?.draft?.documentId ?? documentId;
    const resolvedSnapshot = buildDocumentSnapshot({
      title: resolvedTitle,
      documentType: resolvedDocumentType,
      documentText: resolvedDocumentText,
    });
    const resolvedText = resolvedDocumentText.trim();
    const shouldAllowReuse = options?.allowReuse ?? true;
    const canReuseResolvedDocument =
      Boolean(resolvedDocumentId) && resolvedSnapshot === indexedDocumentSnapshot;

    if (!resolvedText && !resolvedDocumentId) {
      return;
    }

    setIsExplaining(true);
    setDocumentError("");
    try {
      const shouldReuseStoredDocument = shouldAllowReuse && canReuseResolvedDocument;
      const response = await api.explainDocument(
        shouldReuseStoredDocument
          ? {
              document_id: resolvedDocumentId,
              document_type: resolvedDocumentType,
              focus_question: resolvedQuestion,
              title: resolvedTitle || undefined,
            }
          : {
              title: resolvedTitle || undefined,
              content: resolvedText,
              document_type: resolvedDocumentType,
              focus_question: resolvedQuestion,
            },
      );

      setDocumentSummary(response);
      setDocumentId(response.document_id);
      setIndexedDocumentSnapshot(resolvedSnapshot);
      setDocumentTitle(resolvedTitle);
      setDocumentType(resolvedDocumentType);
      setDocumentText(resolvedDocumentText);
      setFocusQuestion(resolvedQuestion);
      persistDocumentFlow({
        documentTitle: resolvedTitle,
        documentType: resolvedDocumentType,
        documentText: resolvedDocumentText,
        documentId: response.document_id,
        documentFocusQuestion: resolvedQuestion,
      });
    } catch (error) {
      if (shouldAllowReuse && canReuseResolvedDocument) {
        await requestDocumentExplanation({
          question: resolvedQuestion,
          allowReuse: false,
          draft: {
            title: resolvedTitle,
            documentType: resolvedDocumentType,
            documentText: resolvedDocumentText,
            documentId: resolvedDocumentId,
          },
        });
        return;
      }

      setDocumentSummary(null);
      setDocumentError(
        error instanceof Error
          ? error.message
          : "Unable to explain this document right now.",
      );
    } finally {
      setIsExplaining(false);
    }
  }

  async function handleDocumentExplain() {
    await requestDocumentExplanation({});
  }

  async function handleDocumentUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    if (!file) {
      return;
    }

    setIsExtractingDocument(true);
    setDocumentError("");
    try {
      const extracted = await api.extractDocument({
        file,
        document_type: documentType,
        title: file.name.replace(/\.[^.]+$/, ""),
      });
      setUploadedDocument(extracted);
      setDocumentTitle(extracted.title);
      setDocumentType(extracted.document_type);
      setDocumentText(extracted.extracted_text);
      setDocumentId("");
      setDocumentSummary(null);
      setIndexedDocumentSnapshot("");
      persistDocumentFlow({
        documentTitle: extracted.title,
        documentType: extracted.document_type,
        documentText: extracted.extracted_text,
        documentId: "",
        documentFocusQuestion: focusQuestion,
      });
      await requestDocumentExplanation({
        allowReuse: false,
        draft: {
          title: extracted.title,
          documentType: extracted.document_type,
          documentText: extracted.extracted_text,
          documentId: "",
        },
      });
    } catch (uploadError) {
      setUploadedDocument(null);
      setDocumentError(
        uploadError instanceof Error
          ? uploadError.message
          : "Unable to extract text from that file right now.",
      );
    } finally {
      setIsExtractingDocument(false);
      event.currentTarget.value = "";
    }
  }

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Checking your account before opening chat...</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="page-shell chat-layout">
      <section className="panel chat-panel">
        <div className="panel-heading">
          <span className="eyebrow">Assistant chat</span>
          <h1>Ask follow-up questions</h1>
          <p>
            This demo chat uses the same symptom and insurance context gathered
            in earlier steps.
          </p>
        </div>

        <div className="conversation">
          {conversation.map((turn, index) => (
            <article
              className={`chat-bubble ${turn.role === "assistant" ? "assistant" : "user"}`}
              key={`${turn.role}-${index}`}
            >
              <strong>{turn.role === "assistant" ? "Assistant" : "You"}</strong>
              <ChatMessageContent content={turn.content} role={turn.role} />
            </article>
          ))}
        </div>

        <form className="chat-form" onSubmit={handleChatSubmit}>
          <textarea
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="What should I do next?"
          />
          <button className="button button-primary" disabled={isSending} type="submit">
            {isSending ? "Sending..." : "Send message"}
          </button>
        </form>
      </section>

      <section className="panel document-panel">
        <div className="panel-heading">
          <span className="eyebrow">Document explainer</span>
          <h2>Upload or paste a report</h2>
          <p>
            Upload a PDF, image, or text file and we will extract the text and
            explain it automatically. You can still paste or edit the text by
            hand, and follow-up questions will reuse the saved vector index.
          </p>
        </div>

        <label className="field">
          <span>Document title</span>
          <input
            value={documentTitle}
            onChange={(event) => {
              const nextTitle = event.target.value;
              setDocumentTitle(nextTitle);
              persistDocumentFlow({
                documentTitle: nextTitle,
                documentType,
                documentText,
                documentId,
                documentFocusQuestion: focusQuestion,
              });
            }}
          />
        </label>

        <label className="field">
          <span>Document text</span>
          <textarea
            rows={10}
            value={documentText}
            onChange={(event) => {
              const nextText = event.target.value;
              setDocumentText(nextText);
              persistDocumentFlow({
                documentTitle,
                documentType,
                documentText: nextText,
                documentId,
                documentFocusQuestion: focusQuestion,
              });
            }}
          />
        </label>

        <label className="field">
          <span>Upload PDF, image, or text file</span>
          <input
            type="file"
            accept=".txt,.md,.json,.csv,.pdf,.png,.jpg,.jpeg,.gif,.webp,image/*,application/pdf,text/plain"
            onChange={handleDocumentUpload}
          />
        </label>

        {isExtractingDocument ? (
          <p className="upload-status-copy">
            Extracting text from uploaded file...
          </p>
        ) : null}

        {!isExtractingDocument && isExplaining && uploadedDocument ? (
          <p className="upload-status-copy">
            Explaining the uploaded document...
          </p>
        ) : null}

        {uploadedDocument ? (
          <div className="info-box">
            <div className="document-meta-row">
              <span className="meta-pill">{uploadedDocument.extraction_method}</span>
              <span className="meta-pill">{uploadedDocument.source_file_name}</span>
            </div>
            <p>{uploadedDocument.extracted_preview}...</p>
            <p className="document-status-copy">
              Upload complete. The explanation is generated automatically from
              the extracted text below.
            </p>
            {uploadedDocument.warnings.map((warning) => (
              <p className="document-warning-copy" key={warning}>
                {warning}
              </p>
            ))}
          </div>
        ) : null}

        <label className="field">
          <span>Focus question</span>
          <input
            value={focusQuestion}
            onChange={(event) => {
              const nextQuestion = event.target.value;
              setFocusQuestion(nextQuestion);
              persistDocumentFlow({
                documentTitle,
                documentType,
                documentText,
                documentId,
                documentFocusQuestion: nextQuestion,
              });
            }}
            placeholder="What matters most?"
          />
        </label>

        {canReuseIndexedDocument ? (
          <p className="document-status-copy">
            Reusing saved document <strong>{documentId}</strong> for follow-up
            questions.
          </p>
        ) : null}

        {isDocumentDirty ? (
          <p className="document-dirty-notice">
            Document text changed. The next explanation will create a fresh
            stored index for this version.
          </p>
        ) : null}

        {documentError ? <p className="error-text">{documentError}</p> : null}

        <div className="form-actions">
          <button
            className="button button-primary"
            disabled={isExplaining || isExtractingDocument}
            onClick={handleDocumentExplain}
            type="button"
          >
            {isExtractingDocument
              ? "Extracting..."
              : isExplaining
              ? "Explaining..."
              : canReuseIndexedDocument
                ? "Ask about saved document"
                : "Index and explain document"}
          </button>
        </div>

        {documentSummary ? (
          <div className="info-box">
            <div className="document-meta-row">
              <span className="meta-pill">
                {documentSummary.indexed_now ? "Indexed just now" : "Using saved index"}
              </span>
              <span className="meta-pill">
                Vector store: {documentSummary.vector_store_backend}
              </span>
            </div>
            <h3>Summary</h3>
            <p>{documentSummary.summary}</p>
            <h4>Important terms</h4>
            <ul className="detail-list">
              {documentSummary.important_terms.map((term) => (
                <li key={term}>{term}</li>
              ))}
            </ul>
            <h4>Questions to ask</h4>
            <ul className="detail-list">
              {documentSummary.follow_up_questions.map((question) => (
                <li key={question}>
                  <button
                    className="chip-button"
                    disabled={isExplaining}
                    onClick={() => requestDocumentExplanation({ question })}
                    type="button"
                  >
                    {question}
                  </button>
                </li>
              ))}
            </ul>
            {documentSummary.supporting_chunks.length ? (
              <>
                <h4>Retrieved snippets</h4>
                <ul className="detail-list supporting-chunk-list">
                  {documentSummary.supporting_chunks.map((chunk) => (
                    <li key={chunk}>{chunk}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        ) : null}
      </section>
    </main>
  );
}
