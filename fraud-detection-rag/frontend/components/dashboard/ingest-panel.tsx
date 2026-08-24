"use client";

import { FormEvent, useState } from "react";
import { CheckCircle2, Loader2, UploadCloud } from "lucide-react";
import { FileDropzone } from "@/components/dashboard/file-dropzone";
import { Button } from "@/components/ui/button";
import { CustomCalendar } from "@/components/ui/custom-calendar";
import { CustomDropdown } from "@/components/ui/custom-dropdown";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ingestDocument } from "@/lib/api";
import {
  CATEGORY_OPTIONS,
  FILE_TYPE_OPTIONS,
  TENANT_OPTIONS,
} from "@/lib/constants";
import {
  buildDocumentId,
  extractTextFromFile,
  inferFileType,
  isAcceptedIngestFile,
} from "@/lib/file-utils";
import { useAuth } from "@/lib/auth-context";

export function IngestPanel() {
  const { user } = useAuth();
  const [content, setContent] = useState("");
  const [source, setSource] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [tenantId, setTenantId] = useState(user?.organization ?? "INSURER-001");
  const [category, setCategory] = useState("fraud-guideline");
  const [fileType, setFileType] = useState("pdf");
  const [documentDate, setDocumentDate] = useState<Date | null>(new Date());
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [fileError, setFileError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleFileSelect(file: File) {
    if (!isAcceptedIngestFile(file)) {
      setFileError("Unsupported file type. Use PDF, TXT, CSV, or DOCX.");
      return;
    }

    setFileError("");
    setSelectedFile(file);
    setIsExtracting(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const extracted = await extractTextFromFile(file);

      if (!extracted.trim()) {
        throw new Error("No readable text found in this file.");
      }

      setContent(extracted);
      setSource(`uploads/${file.name}`);
      setDocumentId(buildDocumentId(file.name));
      setFileType(inferFileType(file.name));
    } catch {
      setFileError(
        "Could not extract text from this file. Try a different format or paste the content below.",
      );
      setContent("");
    } finally {
      setIsExtracting(false);
    }
  }

  function handleClearFile() {
    setSelectedFile(null);
    setFileError("");
    setContent("");
    setSource("");
    setDocumentId("");
    setFileType("pdf");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSuccessMessage("");
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const result = await ingestDocument({
        content,
        source: source || `uploads/${selectedFile?.name ?? "document.txt"}`,
        file_type: fileType,
        tenant_id: tenantId,
        category,
        metadata: {
          document_id: documentId || buildDocumentId(selectedFile?.name ?? "DOC"),
          ...(documentDate
            ? { document_date: documentDate.toISOString().slice(0, 10) }
            : {}),
          ...(selectedFile ? { original_filename: selectedFile.name } : {}),
        },
      });

      setSuccessMessage(
        `Document ingested successfully${result.chunks_created ? ` · ${result.chunks_created} chunks created` : ""}.`,
      );
      setContent("");
      setSelectedFile(null);
      setSource("");
      setDocumentId("");
    } catch {
      setErrorMessage(
        "Ingestion failed. Ensure the FastAPI backend is running and the payload is valid.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="px-6 py-8 lg:px-8">
      <div className="w-full">
        <div className="mb-8">
          <div className="flex items-center gap-2">
            <UploadCloud className="h-5 w-5 text-primary" />
            <h1 className="text-xl font-semibold tracking-tight text-foreground">
              Ingest documents
            </h1>
          </div>
          <p className="mt-2 text-sm leading-7 text-muted">
            Upload files or paste text to add healthcare fraud documents to the
            vector store with tenant, category, and metadata.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-6 rounded-[28px] border border-border bg-card p-6 shadow-[var(--shadow)] md:p-8"
        >
          <FileDropzone
            selectedFile={selectedFile}
            isProcessing={isExtracting}
            error={fileError}
            onFileSelect={handleFileSelect}
            onClear={handleClearFile}
          />

          <Textarea
            label="Document content"
            placeholder="Paste investigation guidelines, claim notes, or policy text..."
            value={content}
            onChange={(event) => setContent(event.target.value)}
            className="min-h-40"
            required
          />

          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Source path"
              value={source}
              onChange={(event) => setSource(event.target.value)}
              placeholder="uploads/fraud-guidelines.pdf"
              required
            />
            <Input
              label="Document ID"
              value={documentId}
              onChange={(event) => setDocumentId(event.target.value)}
              placeholder="DOC-001"
              required
            />
          </div>

          <div className="grid items-start gap-4 overflow-visible md:grid-cols-2">
            <CustomDropdown
              label="Tenant"
              value={tenantId}
              options={TENANT_OPTIONS}
              onChange={setTenantId}
            />
            <CustomDropdown
              label="Category"
              value={category}
              options={CATEGORY_OPTIONS}
              onChange={setCategory}
            />
          </div>

          <div className="grid items-start gap-4 overflow-visible md:grid-cols-2">
            <CustomDropdown
              label="File type"
              value={fileType}
              options={FILE_TYPE_OPTIONS}
              onChange={setFileType}
            />
            <CustomCalendar
              label="Document date"
              value={documentDate}
              onChange={setDocumentDate}
            />
          </div>

          {successMessage ? (
            <div className="flex items-start gap-3 rounded-2xl bg-primary-soft px-4 py-3 text-sm text-primary">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              {successMessage}
            </div>
          ) : null}

          {errorMessage ? (
            <div className="rounded-2xl bg-danger-soft px-4 py-3 text-sm text-danger">
              {errorMessage}
            </div>
          ) : null}

          <Button
            type="submit"
            size="lg"
            className="w-full sm:w-auto"
            disabled={isSubmitting || isExtracting || !content.trim()}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Ingesting document
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4" />
                Ingest into vector store
              </>
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
