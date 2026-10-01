"use client";

import { useId, useRef, useState, type DragEvent } from "react";
import Link from "next/link";
import { AppButton } from "./app-primitives";
import { useAccessToken } from "./app-session";
import { CloseIcon, UploadIcon } from "./icons";
import { isTenantAdmin } from "../lib/navigation";
import {
  DocumentUploadError,
  uploadDocument,
  type UploadedDocument,
} from "../lib/auth";
import { useTenant } from "./tenant-context";

type UploadActionProps = { buttonLabel?: string };

function formatFileSize(size: number): string {
  if (size < 1024) return `${size} bytes`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadAction({
  buttonLabel = "Upload document",
}: UploadActionProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  const inputId = useId();
  const token = useAccessToken();
  const { selectedOrganization, selectedWorkspace, organizationRole } =
    useTenant();
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uploaded, setUploaded] = useState<UploadedDocument | null>(null);

  const canUpload = Boolean(
    token &&
    selectedOrganization &&
    selectedWorkspace &&
    isTenantAdmin(organizationRole),
  );

  function setSelectedFile(nextFile: File | undefined) {
    if (!nextFile) return;
    setFile(nextFile);
    setError("");
    setUploaded(null);
  }

  function openFilePicker() {
    if (fileInput.current) fileInput.current.value = "";
    fileInput.current?.click();
  }

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setDragging(false);
    setSelectedFile(event.dataTransfer.files.item(0) ?? undefined);
  }

  async function submitUpload() {
    if (submitting.current) return;
    if (!file) {
      setError("Choose a file before uploading.");
      return;
    }
    if (
      !token ||
      !selectedOrganization ||
      !selectedWorkspace ||
      !isTenantAdmin(organizationRole)
    ) {
      setError("Select an organization and workspace you can access.");
      return;
    }

    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await uploadDocument(
        token,
        selectedOrganization.id,
        selectedWorkspace.id,
        file,
        new AbortController().signal,
      );
      setUploaded(result);
    } catch (failure) {
      setError(
        failure instanceof DocumentUploadError
          ? failure.message
          : "Upload failed. Try again later.",
      );
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  function resetUpload() {
    setFile(null);
    setError("");
    setUploaded(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  return (
    <>
      <AppButton
        onClick={() => dialog.current?.showModal()}
        disabled={!canUpload}
        aria-describedby={!canUpload ? `${inputId}-unavailable` : undefined}
      >
        <UploadIcon />
        {buttonLabel}
      </AppButton>
      {!canUpload && (
        <span className="upload-unavailable" id={`${inputId}-unavailable`}>
          Select an organization and accessible workspace to add files.
        </span>
      )}
      <dialog
        ref={dialog}
        className="upload-dialog"
        aria-labelledby={`${inputId}-title`}
        onClose={() => setDragging(false)}
      >
        <div className="section-heading upload-dialog-heading">
          <div>
            <h2 id={`${inputId}-title`}>Manual Upload</h2>
            <p>Add files directly to this workspace’s knowledge.</p>
          </div>
          <button
            className="icon-button"
            aria-label="Close upload"
            onClick={() => dialog.current?.close()}
            disabled={busy}
          >
            <CloseIcon />
          </button>
        </div>

        {uploaded ? (
          <section className="upload-success" role="status" aria-live="polite">
            <h3>Upload received</h3>
            <p>
              Status: <strong>{uploaded.status}</strong>. Processing or indexing
              has not been confirmed.
            </p>
            <dl className="upload-metadata">
              <div>
                <dt>File</dt>
                <dd>{uploaded.original_filename}</dd>
              </div>
              <div>
                <dt>Type</dt>
                <dd>{uploaded.mime_type || "Unknown type"}</dd>
              </div>
              <div>
                <dt>Size</dt>
                <dd>
                  {uploaded.size_bytes === null
                    ? "Unknown size"
                    : formatFileSize(uploaded.size_bytes)}
                </dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{uploaded.created_at}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{uploaded.status}</dd>
              </div>
            </dl>
            <div className="upload-actions">
              <AppButton variant="secondary" onClick={resetUpload}>
                Upload another
              </AppButton>
              <Link
                className="app-button primary"
                href="/app/documents"
                onClick={() => dialog.current?.close()}
              >
                Go to Documents
              </Link>
            </div>
          </section>
        ) : (
          <>
            <input
              id={inputId}
              ref={fileInput}
              className="upload-file-input"
              type="file"
              aria-label="Choose a file"
              onChange={(event) =>
                setSelectedFile(event.currentTarget.files?.[0])
              }
            />
            <button
              type="button"
              className={`upload-drop${dragging ? " is-dragging" : ""}`}
              aria-label="Drop a file here or choose a file"
              onClick={openFilePicker}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
            >
              <UploadIcon />
              <strong>{file ? "File selected" : "Drop a file here"}</strong>
              <span>or choose a file from your device</span>
            </button>
            {file && (
              <div className="upload-selected-file" aria-live="polite">
                <div>
                  <strong title={file.name}>{file.name}</strong>
                  <span>
                    {formatFileSize(file.size)} · {file.type || "Unknown type"}
                  </span>
                </div>
                <div className="upload-file-actions">
                  <button
                    type="button"
                    className="inline-link"
                    onClick={openFilePicker}
                  >
                    Replace file
                  </button>
                  <button
                    type="button"
                    className="inline-link"
                    aria-label="Remove selected file"
                    onClick={resetUpload}
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}
            <p className="upload-policy-note">
              File type and size are checked securely when the file is received.
            </p>
            {error && (
              <p className="upload-error" role="alert">
                {error}
              </p>
            )}
            <div className="upload-actions">
              <AppButton
                onClick={submitUpload}
                disabled={!file || busy || !canUpload}
              >
                {busy ? "Uploading…" : "Upload to workspace"}
              </AppButton>
            </div>
            {busy && (
              <p className="upload-progress" role="status">
                Uploading securely…
              </p>
            )}
          </>
        )}
      </dialog>
    </>
  );
}
