"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatMessageContentProps = {
  content: string;
  role: "user" | "assistant" | "system";
};

export function ChatMessageContent({
  content,
  role,
}: ChatMessageContentProps) {
  if (role === "assistant") {
    return (
      <div className="chat-message-content markdown-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="chat-message-content plain-content">
      <p>{content}</p>
    </div>
  );
}

