"use client";

import { useCallback, useState } from "react";
import {
  ApiError,
  deleteDataset as deleteDatasetRequest,
  getApiErrorCode,
  getApiErrorMessage,
  listDatasets,
  previewDataset,
  uploadDataset,
  type DatasetMetadata,
  type DatasetPreviewResponse,
  MAX_UPLOAD_BYTES,
} from "@/lib/api";

export type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "success"; dataset: DatasetMetadata }
  | { status: "error"; message: string; code: string };

export function useDatasets() {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>({ status: "idle" });
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<DatasetPreviewResponse | null>(
    null,
  );
  const [deleteTarget, setDeleteTarget] = useState<DatasetMetadata | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const activeDataset =
    datasets.find((dataset) => dataset.dataset_id === activeDatasetId) ?? null;

  const refreshDatasets = useCallback(async () => {
    setListLoading(true);
    setListError(null);

    try {
      const response = await listDatasets();
      setDatasets(response.datasets);

      setActiveDatasetId((current) => {
        if (current && response.datasets.some((item) => item.dataset_id === current)) {
          return current;
        }

        return response.datasets[0]?.dataset_id ?? null;
      });
    } catch (error) {
      setListError(getApiErrorMessage(error));
      setDatasets([]);
      setActiveDatasetId(null);
    } finally {
      setListLoading(false);
    }
  }, []);

  const selectDataset = useCallback((datasetId: string) => {
    setActiveDatasetId(datasetId);
    setPreviewOpen(false);
    setPreviewData(null);
    setPreviewError(null);
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      return "CSV REQUIRED";
    }

    if (file.size === 0) {
      return "The selected file is empty.";
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      return "Maximum file size: 25 MB.";
    }

    return null;
  }, []);

  const uploadFile = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);

      if (validationError) {
        setUploadState({
          status: "error",
          message: validationError,
          code:
            validationError === "CSV REQUIRED"
              ? "unsupported_file_type"
              : "file_too_large",
        });
        return;
      }

      setUploadState({ status: "uploading" });

      try {
        const response = await uploadDataset(file);
        setUploadState({ status: "success", dataset: response.dataset });
        setDatasets((current) => {
          const filtered = current.filter(
            (item) => item.dataset_id !== response.dataset.dataset_id,
          );
          return [response.dataset, ...filtered];
        });
        setActiveDatasetId(response.dataset.dataset_id);
      } catch (error) {
        setUploadState({
          status: "error",
          message: getApiErrorMessage(error),
          code: getApiErrorCode(error),
        });
      }
    },
    [validateFile],
  );

  const resetUploadState = useCallback(() => {
    setUploadState({ status: "idle" });
  }, []);

  const openPreview = useCallback(async () => {
    if (!activeDataset) {
      return;
    }

    setPreviewOpen(true);
    setPreviewLoading(true);
    setPreviewError(null);

    try {
      const response = await previewDataset(activeDataset.dataset_id, 20);
      setPreviewData(response);
    } catch (error) {
      setPreviewError(getApiErrorMessage(error));
      setPreviewData(null);
    } finally {
      setPreviewLoading(false);
    }
  }, [activeDataset]);

  const closePreview = useCallback(() => {
    setPreviewOpen(false);
    setPreviewData(null);
    setPreviewError(null);
  }, []);

  const requestDelete = useCallback((dataset: DatasetMetadata) => {
    setDeleteTarget(dataset);
    setDeleteError(null);
  }, []);

  const cancelDelete = useCallback(() => {
    setDeleteTarget(null);
    setDeleteError(null);
  }, []);

  const confirmDelete = useCallback(async () => {
    if (!deleteTarget) {
      return;
    }

    setDeleteLoading(true);
    setDeleteError(null);

    try {
      await deleteDatasetRequest(deleteTarget.dataset_id);

      setDatasets((current) => {
        const next = current.filter(
          (item) => item.dataset_id !== deleteTarget.dataset_id,
        );

        setActiveDatasetId((activeId) => {
          if (activeId !== deleteTarget.dataset_id) {
            return activeId;
          }

          return next[0]?.dataset_id ?? null;
        });

        return next;
      });

      if (previewData?.dataset_id === deleteTarget.dataset_id) {
        closePreview();
      }

      setDeleteTarget(null);
    } catch (error) {
      setDeleteError(getApiErrorMessage(error));
    } finally {
      setDeleteLoading(false);
    }
  }, [closePreview, deleteTarget, previewData]);

  return {
    datasets,
    activeDataset,
    activeDatasetId,
    uploadState,
    listLoading,
    listError,
    previewOpen,
    previewLoading,
    previewError,
    previewData,
    deleteTarget,
    deleteLoading,
    deleteError,
    refreshDatasets,
    selectDataset,
    uploadFile,
    resetUploadState,
    openPreview,
    closePreview,
    requestDelete,
    cancelDelete,
    confirmDelete,
  };
}

export type UseDatasetsReturn = ReturnType<typeof useDatasets>;

export function isApiOfflineError(error: unknown): boolean {
  return error instanceof ApiError && error.code === "network_error";
}
