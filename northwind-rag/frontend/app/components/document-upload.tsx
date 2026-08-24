"use client";

import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  listDocuments,
  uploadDocumentFile,
  uploadDocumentText,
} from "../lib/api";
import type { DocumentUploadResponse } from "../lib/types";

type Tab = "text" | "markdown" | "pdf";

interface DocumentUploadProps {
  onIndexed: () => void;
}

export function DocumentUpload({ onIndexed }: DocumentUploadProps) {
  const [tab, setTab] = useState<Tab>("text");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<DocumentUploadResponse | null>(null);
  const [documents, setDocuments] = useState<string[]>([]);

  const refreshDocuments = useCallback(async () => {
    try {
      const { documents: docs } = await listDocuments();
      setDocuments(docs);
    } catch {
      // List failure is non-fatal; upload/ask still work.
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    listDocuments()
      .then(({ documents: docs }) => {
        if (!cancelled) setDocuments(docs);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSuccess = useCallback(
    (result: DocumentUploadResponse) => {
      setSuccess(result);
      setError(null);
      setTitle("");
      setText("");
      onIndexed();
      void refreshDocuments();
    },
    [onIndexed, refreshDocuments],
  );

  const submitText = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedText = text.trim();
    if (!trimmedTitle || !trimmedText) {
      setError("Title and text are required.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      handleSuccess(await uploadDocumentText(trimmedTitle, trimmedText));
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Failed to index document.",
      );
    } finally {
      setLoading(false);
    }
  };

  const submitFile = async (file: File | undefined, kind: Tab) => {
    if (!file) {
      setError("Choose a file first.");
      return;
    }

    const ext = kind === "markdown" ? ".md" : ".pdf";
    if (!file.name.toLowerCase().endsWith(ext)) {
      setError(`Only ${ext} files are supported in this tab.`);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      handleSuccess(await uploadDocumentFile(file));
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Failed to index document.",
      );
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "text", label: "Text" },
    { id: "markdown", label: "Markdown" },
    { id: "pdf", label: "PDF" },
  ];

  return (
    <section className="flex flex-col gap-4 rounded-lg border border-line bg-surface p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium">Add documents</h2>
          <p className="mt-1 text-sm text-muted">
            New content is chunked and indexed into Chroma immediately.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              setTab(id);
              setError(null);
              setSuccess(null);
            }}
            className={`cursor-pointer rounded-full border px-3 py-1 text-sm ${
              tab === id
                ? "border-accent bg-accent-soft text-accent"
                : "border-line text-muted hover:text-foreground"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "text" && (
        <form onSubmit={(e) => void submitText(e)} className="flex flex-col gap-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Document title"
            aria-label="Document title"
            className="rounded-lg border border-line bg-background px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste document text…"
            aria-label="Document text"
            rows={5}
            className="resize-y rounded-lg border border-line bg-background px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={loading}
            className="self-start cursor-pointer rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 disabled:opacity-60"
          >
            {loading ? "Indexing…" : "Add & index"}
          </button>
        </form>
      )}

      {tab === "markdown" && (
        <div className="flex flex-col gap-3">
          <input
            type="file"
            accept=".md"
            aria-label="Markdown file"
            disabled={loading}
            onChange={(e) => void submitFile(e.target.files?.[0], "markdown")}
            className="text-sm text-muted file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line file:bg-background file:px-3 file:py-1.5 file:text-sm file:text-foreground"
          />
          {loading && <p className="text-sm text-muted">Indexing…</p>}
        </div>
      )}

      {tab === "pdf" && (
        <div className="flex flex-col gap-3">
          <input
            type="file"
            accept=".pdf"
            aria-label="PDF file"
            disabled={loading}
            onChange={(e) => void submitFile(e.target.files?.[0], "pdf")}
            className="text-sm text-muted file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line file:bg-background file:px-3 file:py-1.5 file:text-sm file:text-foreground"
          />
          {loading && <p className="text-sm text-muted">Indexing…</p>}
        </div>
      )}

      {error && (
        <p className="text-sm text-warning-text">{error}</p>
      )}

      {success && (
        <p className="text-sm text-muted">
          Added{" "}
          <span className="font-mono text-foreground">{success.source}</span>
          {" — "}
          {success.chunks_added} chunk{success.chunks_added === 1 ? "" : "s"} (
          {success.total_chunks} total)
        </p>
      )}

      {documents.length > 0 && (
        <div className="border-t border-line pt-4">
          <p className="text-xs tracking-wide text-muted uppercase">
            Indexed documents
          </p>
          <ul className="mt-2 flex flex-col gap-1 font-mono text-xs text-foreground/80">
            {documents.map((doc) => (
              <li key={doc}>{doc}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
