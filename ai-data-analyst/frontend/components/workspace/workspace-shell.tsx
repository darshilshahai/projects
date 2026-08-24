"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PanelLeft } from "lucide-react";
import { checkHealth } from "@/lib/api";
import { useDatasets } from "@/hooks/use-datasets";
import { Brand } from "@/components/shared";
import { AnalysisPanel } from "./analysis-panel";
import { DatasetPreviewPanel } from "./dataset-preview";
import { DatasetSidebar } from "./dataset-sidebar";
import { DeleteDatasetDialog } from "./delete-dataset-dialog";
import { EngineOfflineBanner } from "./engine-offline-banner";
import { UploadZone } from "./upload-zone";
import { WorkspaceHeader } from "./workspace-header";

export function WorkspaceShell() {
  const {
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
    selectDataset,
    uploadFile,
    resetUploadState,
    openPreview,
    closePreview,
    requestDelete,
    cancelDelete,
    confirmDelete,
    refreshDatasets,
  } = useDatasets();

  const [engineOnline, setEngineOnline] = useState(false);
  const [engineChecked, setEngineChecked] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    void refreshDatasets();
  }, [refreshDatasets]);

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const health = await checkHealth();
        if (!cancelled) {
          setEngineOnline(health.status === "healthy");
        }
      } catch {
        if (!cancelled) {
          setEngineOnline(false);
        }
      } finally {
        if (!cancelled) {
          setEngineChecked(true);
        }
      }
    }

    void loadHealth();
    const interval = window.setInterval(() => {
      void loadHealth();
    }, 30000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const showEmptyWorkspace = !listLoading && datasets.length === 0;
  const apiOffline = engineChecked && !engineOnline;

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-background">
      <a
        href="#workspace-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:border focus:border-accent focus:bg-background focus:px-3 focus:py-2 focus:font-mono focus:text-[10px] focus:tracking-[0.12em] focus:uppercase"
      >
        Skip to workspace
      </a>

      <div className="shrink-0 border-b border-border-subtle px-4 py-3 sm:px-6">
        <div className="flex items-center justify-between gap-3">
          <Brand href="/" />
          {!showEmptyWorkspace ? (
            <button
              type="button"
              className="inline-flex items-center gap-2 border border-border-subtle px-2.5 py-2 font-mono text-[10px] tracking-[0.12em] text-muted uppercase transition-colors duration-150 hover:border-border hover:text-foreground lg:hidden"
              aria-expanded={sidebarOpen}
              aria-controls="dataset-sidebar"
              onClick={() => setSidebarOpen((current) => !current)}
            >
              <PanelLeft className="size-3.5" aria-hidden="true" />
              Dataset
            </button>
          ) : null}
        </div>
      </div>

      <WorkspaceHeader
        dataset={activeDataset}
        engineOnline={engineChecked ? engineOnline : false}
      />

      {apiOffline && showEmptyWorkspace ? <EngineOfflineBanner /> : null}

      {previewOpen && activeDataset ? (
        <DatasetPreviewPanel
          dataset={activeDataset}
          open={previewOpen}
          loading={previewLoading}
          error={previewError}
          preview={previewData}
          onClose={closePreview}
        />
      ) : null}

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
        {!showEmptyWorkspace ? (
          <>
            {sidebarOpen ? (
              <button
                type="button"
                aria-label="Close dataset sidebar"
                className="fixed inset-0 z-40 bg-background/80 lg:hidden"
                onClick={() => setSidebarOpen(false)}
              />
            ) : null}

            <div
              id="dataset-sidebar"
              className={
                sidebarOpen
                  ? "fixed inset-y-0 left-0 z-50 flex w-[min(100vw,320px)] flex-col overflow-hidden border-r border-border-subtle bg-background pt-30 lg:static lg:z-auto lg:flex lg:h-full lg:w-auto lg:pt-0"
                  : "hidden lg:flex lg:h-full"
              }
            >
              <DatasetSidebar
                datasets={datasets}
                activeDataset={activeDataset}
                activeDatasetId={activeDatasetId}
                uploadState={uploadState}
                listLoading={listLoading}
                onSelectDataset={(datasetId) => {
                  selectDataset(datasetId);
                  setSidebarOpen(false);
                }}
                onUpload={uploadFile}
                onResetUploadState={resetUploadState}
                onPreview={() => void openPreview()}
                onDelete={requestDelete}
              />
            </div>
          </>
        ) : null}

        <main
          id="workspace-main"
          className="flex min-h-0 flex-1 flex-col overflow-hidden"
        >
          {showEmptyWorkspace ? (
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
              <div className="flex min-h-full items-center justify-center px-6 py-16 md:px-10">
                <div className="w-full max-w-2xl">
                  {listError && !apiOffline ? (
                    <div className="mb-6 border border-danger/30 bg-danger-muted px-4 py-3">
                      <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
                        DATASET LIST FAILED
                      </p>
                      <p className="mt-2 text-sm text-muted-strong">{listError}</p>
                      <button
                        type="button"
                        onClick={() => void refreshDatasets()}
                        className="mt-3 font-mono text-[10px] tracking-[0.12em] text-muted uppercase transition-colors duration-150 hover:text-foreground"
                      >
                        RETRY
                      </button>
                    </div>
                  ) : null}

                  <UploadZone
                    onUpload={uploadFile}
                    uploadState={uploadState}
                    onResetUploadState={resetUploadState}
                    featured
                    disabled={apiOffline}
                  />
                </div>
              </div>
            </div>
          ) : (
            <>
              {listError && !apiOffline ? (
                <div className="shrink-0 border-b border-border-subtle bg-danger-muted px-4 py-3 md:px-6">
                  <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
                    DATASET LIST FAILED
                  </p>
                  <p className="mt-1 text-sm text-muted-strong">{listError}</p>
                </div>
              ) : null}

              <AnalysisPanel
                key={activeDatasetId ?? "no-dataset"}
                activeDataset={activeDataset}
                engineOnline={engineOnline}
              />
            </>
          )}
        </main>
      </div>

      <DeleteDatasetDialog
        dataset={deleteTarget}
        loading={deleteLoading}
        error={deleteError}
        onCancel={cancelDelete}
        onConfirm={() => void confirmDelete()}
      />

      <div className="shrink-0 border-t border-border-subtle px-4 py-3 sm:px-6">
        <Link
          href="/"
          className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase transition-colors duration-150 hover:text-foreground"
        >
          ← Back to landing
        </Link>
      </div>
    </div>
  );
}
