"use client";

import { FileText, UploadCloud, X } from "lucide-react";
import {
  useCallback,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
} from "react";
import { Button } from "@/components/ui/button";
import {
  ACCEPTED_INGEST_EXTENSIONS,
  formatFileSize,
  isAcceptedIngestFile,
} from "@/lib/file-utils";
import { cn } from "@/lib/utils";

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  onClear: () => void;
  selectedFile: File | null;
  isProcessing?: boolean;
  error?: string;
}

export function FileDropzone({
  onFileSelect,
  onClear,
  selectedFile,
  isProcessing = false,
  error,
}: FileDropzoneProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState("");

  const accept = ACCEPTED_INGEST_EXTENSIONS.join(",");

  const handleFile = useCallback(
    (file: File | null | undefined) => {
      if (!file) return;

      if (!isAcceptedIngestFile(file)) {
        setLocalError("Unsupported file type. Use PDF, TXT, CSV, or DOCX.");
        return;
      }

      setLocalError("");
      onFileSelect(file);
    },
    [onFileSelect],
  );

  function handleDragEnter(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    handleFile(event.dataTransfer.files[0]);
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    handleFile(event.target.files?.[0]);
    event.target.value = "";
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-foreground">
        Upload document
      </label>

      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative rounded-[24px] border-2 border-dashed px-6 py-10 transition-all",
          isDragging
            ? "border-primary bg-primary-soft/40"
            : "border-border bg-muted-bg/40 hover:border-primary/40 hover:bg-muted-bg/70",
          selectedFile && "border-solid border-primary/30 bg-primary-soft/20 py-6",
        )}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={accept}
          className="sr-only"
          onChange={handleInputChange}
        />

        {selectedFile ? (
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary-soft text-primary">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-foreground">
                  {selectedFile.name}
                </p>
                <p className="mt-1 text-xs text-muted">
                  {formatFileSize(selectedFile.size)}
                  {isProcessing ? " · Extracting text..." : " · Ready to ingest"}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => inputRef.current?.click()}
                disabled={isProcessing}
              >
                Replace file
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setLocalError("");
                  onClear();
                }}
                disabled={isProcessing}
              >
                <X className="h-4 w-4" />
                Remove
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center">
            <div
              className={cn(
                "mb-4 flex h-14 w-14 items-center justify-center rounded-2xl transition-colors",
                isDragging ? "bg-primary text-white" : "bg-card text-primary",
              )}
            >
              <UploadCloud className="h-6 w-6" />
            </div>

            <p className="text-sm font-medium text-foreground">
              Drag and drop your file here
            </p>
            <p className="mt-2 max-w-md text-sm leading-6 text-muted">
              Supports PDF, TXT, CSV, and DOCX. Text is extracted in your browser
              before ingestion.
            </p>

            <div className="mt-5 flex flex-col gap-2 sm:flex-row">
              <Button
                type="button"
                size="sm"
                onClick={() => inputRef.current?.click()}
              >
                Browse files
              </Button>
              <p className="self-center text-xs text-muted">
                or drop a file anywhere in this area
              </p>
            </div>
          </div>
        )}
      </div>

      {error || localError ? (
        <p className="rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger">
          {error || localError}
        </p>
      ) : null}
    </div>
  );
}
