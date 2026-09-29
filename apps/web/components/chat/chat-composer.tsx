"use client";

import { useEffect, useId, useRef, type RefObject } from "react";
import { SendIcon } from "../icons";

export type ChatComposerProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  disabled?: boolean;
  inputRef?: RefObject<HTMLTextAreaElement | null>;
};

/** Submission stays unavailable until a real submit handler is supplied. */
export function ChatComposer({
  value,
  onChange,
  onSubmit,
  disabled = false,
  inputRef,
}: ChatComposerProps) {
  const localRef = useRef<HTMLTextAreaElement>(null);
  const ref = inputRef ?? localRef;
  const id = useId();
  const canSend = !disabled && Boolean(onSubmit) && Boolean(value.trim());
  useEffect(() => {
    const input = ref.current;
    if (!input) return;
    function resize() {
      if (!input) return;
      input.style.height = "auto";
      input.style.height = `${Math.min(input.scrollHeight, 200)}px`;
    }
    resize();
    const observer = new ResizeObserver(resize);
    // Observe width changes without creating a textarea resize feedback loop.
    if (input.parentElement)
      observer.observe(input.parentElement, { box: "border-box" });
    return () => observer.disconnect();
  }, [value, ref]);
  return (
    <form
      className="chat-composer"
      onSubmit={(event) => {
        event.preventDefault();
        if (canSend) onSubmit?.();
      }}
    >
      <div className="chat-input-surface">
        <label className="sr-only" htmlFor={id}>
          Ask a question
        </label>
        <textarea
          id={id}
          ref={ref}
          value={value}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
          rows={2}
          maxLength={4000}
          placeholder="Ask anything about your organization…"
          aria-describedby={`${id}-hint`}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              if (canSend) onSubmit?.();
            }
          }}
        />
        <div className="chat-composer-tools">
          <span>
            {onSubmit
              ? "Enter to send · Shift+Enter for a new line"
              : "Answering coming soon"}
          </span>
          <button
            type="submit"
            disabled={!canSend}
            aria-label={
              onSubmit ? "Send question" : "Send question — coming soon"
            }
          >
            <SendIcon />
          </button>
        </div>
      </div>
      <p className="chat-composer-hint" id={`${id}-hint`}>
        {onSubmit
          ? "Check important information against its sources."
          : "Draft only. Nothing is sent or saved. Shift+Enter adds a new line."}
      </p>
    </form>
  );
}
