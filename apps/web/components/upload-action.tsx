"use client";
import { useRef } from "react";
import Link from "next/link";
import { AppButton } from "./app-primitives";
import { UploadIcon, CloseIcon } from "./icons";
export function UploadAction() {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <AppButton onClick={() => dialog.current?.showModal()}>
        <UploadIcon />
        Upload document
      </AppButton>
      <dialog
        ref={dialog}
        className="upload-dialog"
        aria-labelledby="upload-title"
      >
        <div className="section-heading">
          <h2 id="upload-title">Upload a document</h2>
          <button
            className="icon-button"
            aria-label="Close upload"
            onClick={() => dialog.current?.close()}
          >
            <CloseIcon />
          </button>
        </div>
        <div className="upload-drop">
          <UploadIcon />
          <h3>Connect a workspace first</h3>
          <p>
            Manual uploads are available through your organization’s setup.
            Workspace selection in this app is still being connected.
          </p>
          <button className="app-button secondary" disabled>
            Choose a file
          </button>
        </div>
        <p>
          Ask your administrator about workspace access. File uploads from this
          screen are not available yet.
        </p>
        <Link
          className="inline-link"
          href="/app/settings"
          onClick={() => dialog.current?.close()}
        >
          View workspace settings
        </Link>
      </dialog>
    </>
  );
}
