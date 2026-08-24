"use client";

import { useEffect } from "react";
import type { DatasetMetadata } from "@/lib/api";

type DeleteDatasetDialogProps = {
  dataset: DatasetMetadata | null;
  loading: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
};

export function DeleteDatasetDialog({
  dataset,
  loading,
  error,
  onCancel,
  onConfirm,
}: DeleteDatasetDialogProps) {
  useEffect(() => {
    if (!dataset) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCancel();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [dataset, onCancel]);

  if (!dataset) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 px-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-dataset-title"
        className="w-full max-w-md border border-border-subtle bg-background-panel p-6"
      >
        <h2
          id="delete-dataset-title"
          className="text-lg font-medium text-foreground"
        >
          Delete {dataset.original_filename}?
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          This removes the locally stored dataset from this workspace.
        </p>

        {error ? (
          <p className="mt-4 font-mono text-[10px] tracking-[0.12em] text-danger uppercase">
            {error}
          </p>
        ) : null}

        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="landing-cta landing-cta-secondary"
          >
            CANCEL
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="landing-cta border-danger/30 text-danger hover:border-danger hover:text-danger"
          >
            {loading ? "DELETING..." : "DELETE DATASET"}
          </button>
        </div>
      </div>
    </div>
  );
}
