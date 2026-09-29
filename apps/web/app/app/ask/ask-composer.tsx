"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { AskIcon, DocumentsIcon } from "../../../components/icons";
import { ChatComposer } from "../../../components/chat/chat-composer";
import { ConversationViewport } from "../../../components/chat/conversation";

const prompts = [
  "Summarize a policy for my team",
  "Find the steps in a process",
  "Compare information across documents",
  "Explain this using company sources",
];
export function AskComposer() {
  const [draft, setDraft] = useState("");
  const input = useRef<HTMLTextAreaElement>(null);
  return (
    <ConversationViewport
      empty
      composer={
        <>
          <ChatComposer value={draft} onChange={setDraft} inputRef={input} />
          <div
            className="chat-starter-prompts"
            aria-label="Suggested questions"
          >
            {prompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => {
                  setDraft(prompt);
                  input.current?.focus();
                }}
              >
                <DocumentsIcon />
                {prompt}
              </button>
            ))}
          </div>
        </>
      }
    >
      <div className="chat-welcome">
        <span className="chat-welcome-mark">
          <AskIcon />
        </span>
        <h1>Ask Bismark</h1>
        <p>A clearer view of your organization’s knowledge.</p>
        <div className="chat-context-hint">
          <DocumentsIcon />
          <span>Answers will use your authorized workspace sources.</span>
        </div>
        <Link className="chat-context-link" href="/app/sources">
          Explore knowledge sources
        </Link>
      </div>
    </ConversationViewport>
  );
}
