/** @jsxImportSource react */
"use client";

import React, { type ReactNode } from "react";
import { DocumentsIcon, ArrowRightIcon } from "../icons";

export function ConversationViewport({
  children,
  composer,
  empty = false,
}: {
  children: ReactNode;
  composer: ReactNode;
  empty?: boolean;
}) {
  return (
    <section
      className={`conversation-viewport${empty ? " is-empty" : ""}`}
      aria-label="Conversation workspace"
    >
      <div
        className="conversation-scroll"
        role="region"
        aria-label={empty ? "Getting started" : "Messages"}
        tabIndex={0}
      >
        <div className="conversation-column">{children}</div>
      </div>
      <div className="conversation-dock">
        <div className="conversation-column">{composer}</div>
      </div>
    </section>
  );
}
export function UserMessage({ children }: { children: ReactNode }) {
  return (
    <article className="chat-message user-message" aria-label="Your message">
      <span className="message-author">You</span>
      <div className="user-message-content">{children}</div>
    </article>
  );
}
export function AssistantMessage({
  children,
  sources,
  actions,
  followUps,
}: {
  children: ReactNode;
  sources?: ReactNode;
  actions?: ReactNode;
  followUps?: ReactNode;
}) {
  return (
    <article
      className="chat-message assistant-message"
      aria-label="Bismark response"
    >
      <span className="message-author">
        <span className="message-mark" aria-hidden="true">
          B
        </span>
        Bismark
      </span>
      <div className="answer-content">{children}</div>
      {sources && (
        <section className="answer-sources" aria-label="Sources">
          <h2>Sources</h2>
          <div className="citation-list">{sources}</div>
        </section>
      )}
      {actions}
      {followUps}
    </article>
  );
}
export function ResponseActions({
  onCopy,
  onRegenerate,
  onHelpful,
  onNotHelpful,
}: {
  onCopy?: () => void;
  onRegenerate?: () => void;
  onHelpful?: () => void;
  onNotHelpful?: () => void;
}) {
  const actions = [
    { label: "Copy answer", handler: onCopy },
    { label: "Regenerate", handler: onRegenerate },
    { label: "Helpful", handler: onHelpful },
    { label: "Not helpful", handler: onNotHelpful },
  ];
  return (
    <div className="response-actions" role="group" aria-label="Answer actions">
      {actions.map(({ label, handler }) => (
        <button
          type="button"
          key={label}
          onClick={handler}
          disabled={!handler}
          title={!handler ? `${label} — unavailable` : label}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
export function SourceCitation({
  name,
  page,
  section,
  context,
  onView,
}: {
  name: string;
  page?: number;
  section?: string;
  context?: string;
  onView?: () => void;
}) {
  return (
    <button
      type="button"
      className="source-citation"
      onClick={onView}
      disabled={!onView}
      aria-label={`${onView ? "View source" : "Source preview unavailable"}: ${name}`}
    >
      <DocumentsIcon />
      <span>
        <strong>{name}</strong>
        {(page !== undefined || section) && (
          <span className="citation-location">
            {[page !== undefined ? `p. ${page}` : null, section]
              .filter(Boolean)
              .join(" · ")}
          </span>
        )}
        {context && <span className="citation-context">{context}</span>}
      </span>
      <ArrowRightIcon />
    </button>
  );
}
export function FollowUpSuggestions({
  suggestions,
  onSelect,
}: {
  suggestions: string[];
  onSelect?: (value: string) => void;
}) {
  if (!suggestions.length) return null;
  return (
    <section
      className="follow-up-suggestions"
      aria-label="Follow-up suggestions"
    >
      <h2>You might also ask</h2>
      {suggestions.map((suggestion, index) => (
        <button
          type="button"
          key={`${index}-${suggestion}`}
          disabled={!onSelect}
          onClick={() => onSelect?.(suggestion)}
        >
          {suggestion}
          <ArrowRightIcon />
        </button>
      ))}
    </section>
  );
}
