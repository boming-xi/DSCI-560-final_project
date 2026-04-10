"use client";

import { FormEvent, useMemo, useState } from "react";

import { ChatMessageContent } from "@/components/ChatMessageContent";
import { api } from "@/lib/api";
import { getFlowState } from "@/lib/flow";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import type { ChatTurn, DocumentExplainResponse } from "@/lib/types";

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
    "CBC results: WBC slightly elevated. Mild inflammation noted. Follow up if fever persists."
  );
  const [documentSummary, setDocumentSummary] = useState<DocumentExplainResponse | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);

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

  async function handleDocumentExplain() {
    if (!documentText.trim()) {
      return;
    }

    setIsExplaining(true);
    try {
      const response = await api.explainDocument({
        title: "Lab report notes",
        content: documentText,
      });
      setDocumentSummary(response);
    } catch {
      setDocumentSummary(null);
    } finally {
      setIsExplaining(false);
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
          <h2>Paste report text</h2>
          <p>Use this area to demo plain-language explanation of medical documents.</p>
        </div>

        <textarea
          rows={10}
          value={documentText}
          onChange={(event) => setDocumentText(event.target.value)}
        />
        <div className="form-actions">
          <button
            className="button button-primary"
            disabled={isExplaining}
            onClick={handleDocumentExplain}
            type="button"
          >
            {isExplaining ? "Explaining..." : "Explain document"}
          </button>
        </div>

        {documentSummary ? (
          <div className="info-box">
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
                <li key={question}>{question}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>
    </main>
  );
}
