"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import type { DatasetMetadata, DatasetPreviewResponse } from "@/lib/api";
import { formatNumber } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type DatasetPreviewProps = {
  dataset: DatasetMetadata;
  open: boolean;
  loading: boolean;
  error: string | null;
  preview: DatasetPreviewResponse | null;
  onClose: () => void;
};

export function DatasetPreviewPanel({
  dataset,
  open,
  loading,
  error,
  preview,
  onClose,
}: DatasetPreviewProps) {
  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  const columns =
    preview && preview.rows.length > 0
      ? Object.keys(preview.rows[0])
      : dataset.profile.columns.map((column) => column.name);

  const returnedRows = preview?.returned_rows ?? 0;
  const totalRows = dataset.profile.row_count;

  return (
    <div className="border-b border-border-subtle bg-background-panel">
      <div className="flex items-center justify-between gap-4 border-b border-border-subtle px-4 py-3 md:px-6">
        <div>
          <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
            Dataset preview
          </p>
          <p className="mt-1 text-sm text-foreground">{dataset.original_filename}</p>
        </div>

        <div className="flex items-center gap-4">
          <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
            {returnedRows} / {formatNumber(totalRows)} rows
          </p>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center border border-border-subtle p-2 text-muted transition-colors duration-150 hover:border-border hover:text-foreground"
            aria-label="Close dataset preview"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="px-4 py-4 md:px-6">
        {loading ? (
          <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase animate-pulse">
            Reading dataset...
          </p>
        ) : null}

        {error ? (
          <div className="border border-danger/30 bg-danger-muted px-4 py-3">
            <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
              Preview failed
            </p>
            <p className="mt-2 text-sm text-muted-strong">{error}</p>
          </div>
        ) : null}

        {!loading && !error && preview ? (
          <div className="overflow-x-auto border border-border-subtle">
            <table className="min-w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-border-subtle">
                  {columns.map((column) => (
                    <th
                      key={column}
                      className="sticky top-0 bg-background-panel px-4 py-3 font-mono text-[10px] tracking-[0.12em] text-muted uppercase"
                    >
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, rowIndex) => (
                  <tr
                    key={`${dataset.dataset_id}-${rowIndex}`}
                    className="border-b border-border-subtle last:border-b-0"
                  >
                    {columns.map((column) => (
                      <td
                        key={`${rowIndex}-${column}`}
                        className={cn(
                          "px-4 py-3 text-sm text-muted-strong",
                          typeof row[column] === "number" && "text-right font-mono tabular-nums",
                        )}
                      >
                        {formatCellValue(row[column])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}
