"use client";

import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { TechnicalLabel } from "@/components/shared";
import type { UploadState } from "@/hooks/use-datasets";
import { cn } from "@/lib/utils/cn";

type UploadZoneProps = {
  onUpload: (file: File) => void;
  uploadState: UploadState;
  onResetUploadState?: () => void;
  compact?: boolean;
  featured?: boolean;
  disabled?: boolean;
  className?: string;
};

export function UploadZone({
  onUpload,
  uploadState,
  onResetUploadState,
  compact = false,
  featured = false,
  disabled = false,
  className,
}: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) {
        return;
      }

      onUpload(file);
    },
    [onUpload],
  );

  const isUploading = uploadState.status === "uploading";
  const hasError = uploadState.status === "error";

  return (
    <div
      className={cn(
        "space-y-4",
        featured && "border border-accent/30 bg-accent-muted/40 p-4",
        className,
      )}
    >
      {featured ? (
        <div className="space-y-1">
          <TechnicalLabel tone="accent">Add CSV</TechnicalLabel>
          <p className="text-sm text-muted-strong">
            Upload a dataset to inspect schema and run analysis.
          </p>
        </div>
      ) : null}

      {!compact && !featured ? (
        <div className="space-y-3 text-center md:text-left">
          <TechnicalLabel tone="accent">DATASET / 00</TechnicalLabel>
          <h2 className="text-display text-3xl text-foreground md:text-4xl">
            Start with the data.
          </h2>
          <p className="max-w-md text-sm leading-relaxed text-muted md:text-base">
            Upload a CSV file to inspect its schema and begin asking questions.
          </p>
        </div>
      ) : null}

      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload CSV dataset"
        aria-disabled={disabled}
        onKeyDown={(event) => {
          if (disabled) {
            return;
          }

          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        onClick={() => {
          if (!disabled) {
            inputRef.current?.click();
          }
        }}
        onDragOver={(event) => {
          if (disabled) {
            return;
          }

          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(event) => {
          if (disabled) {
            return;
          }

          event.preventDefault();
          setDragOver(false);
          handleFile(event.dataTransfer.files[0]);
        }}
        className={cn(
          "relative border border-dashed px-6 transition-colors duration-150 focus-visible:outline-none",
          disabled
            ? "cursor-not-allowed opacity-50"
            : "cursor-pointer focus-visible:outline-none",
          featured
            ? "border-accent/50 bg-background/40 py-8 hover:border-accent hover:bg-accent-muted/60"
            : dragOver
              ? "border-accent bg-accent-muted py-12"
              : "border-border-subtle py-12 hover:border-border hover:bg-background-panel/40",
          compact && !featured && "py-8",
          featured && dragOver && "border-accent bg-accent-muted",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          disabled={disabled}
          onChange={(event) => {
            handleFile(event.target.files?.[0]);
            event.target.value = "";
          }}
        />

        <div className="flex flex-col items-center gap-4 text-center">
          <Upload
            className={cn(
              "size-5",
              featured || dragOver ? "text-accent" : "text-muted",
            )}
            aria-hidden="true"
          />
          <div className="space-y-2">
            <p
              className={cn(
                "font-mono text-[11px] tracking-[0.14em] uppercase",
                featured ? "text-accent" : "text-foreground",
              )}
            >
              Drop CSV here
            </p>
            <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
              or click to browse
            </p>
          </div>
          <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
            CSV · MAX 25MB
          </p>
        </div>

        {isUploading ? (
          <div className="absolute inset-x-0 bottom-0 h-px overflow-hidden bg-border-subtle">
            <div className="h-full w-1/3 animate-[upload-progress_1.2s_ease-in-out_infinite] bg-accent" />
          </div>
        ) : null}
      </div>

      {hasError ? (
        <div className="border border-danger/30 bg-danger-muted px-4 py-3">
          <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
            {uploadState.code === "file_too_large"
              ? "FILE REJECTED"
              : uploadState.code === "unsupported_file_type"
                ? "CSV REQUIRED"
                : "UPLOAD FAILED"}
          </p>
          <p className="mt-2 text-sm text-muted-strong">{uploadState.message}</p>
          {onResetUploadState ? (
            <button
              type="button"
              onClick={onResetUploadState}
              className="mt-3 font-mono text-[10px] tracking-[0.12em] text-muted uppercase transition-colors duration-150 hover:text-foreground"
            >
              DISMISS
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
