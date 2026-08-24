import type { DatasetMetadata } from "@/lib/api";
import { DatasetList } from "./dataset-list";
import { DatasetSummary } from "./dataset-summary";
import { SchemaList } from "./schema-list";
import { UploadZone } from "./upload-zone";
import type { UploadState } from "@/hooks/use-datasets";
import { cn } from "@/lib/utils/cn";

type DatasetSidebarProps = {
  datasets: DatasetMetadata[];
  activeDataset: DatasetMetadata | null;
  activeDatasetId: string | null;
  uploadState: UploadState;
  listLoading: boolean;
  onSelectDataset: (datasetId: string) => void;
  onUpload: (file: File) => void;
  onResetUploadState: () => void;
  onPreview: () => void;
  onDelete: (dataset: DatasetMetadata) => void;
  className?: string;
};

export function DatasetSidebar({
  datasets,
  activeDataset,
  activeDatasetId,
  uploadState,
  listLoading,
  onSelectDataset,
  onUpload,
  onResetUploadState,
  onPreview,
  onDelete,
  className,
}: DatasetSidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full max-h-[45vh] min-h-0 shrink-0 flex-col overflow-hidden border-b border-border-subtle bg-background lg:max-h-none lg:w-75 lg:shrink-0 lg:border-r lg:border-b-0 xl:w-[320px]",
        className,
      )}
    >
      <div className="scrollbar-hidden min-h-0 flex-1 overflow-y-auto overscroll-contain p-5">
        <div className="space-y-6">
          <UploadZone
            onUpload={onUpload}
            uploadState={uploadState}
            onResetUploadState={onResetUploadState}
            featured
            compact
          />

          {listLoading ? (
            <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase animate-pulse">
              Inspecting datasets...
            </p>
          ) : null}

          {!listLoading && datasets.length > 0 ? (
            <>
              <DatasetList
                datasets={datasets}
                activeDatasetId={activeDatasetId}
                onSelect={onSelectDataset}
              />

              {activeDataset ? (
                <>
                  <DatasetSummary
                    dataset={activeDataset}
                    onPreview={onPreview}
                    onDelete={() => onDelete(activeDataset)}
                  />
                  <SchemaList columns={activeDataset.profile.columns} />
                </>
              ) : null}
            </>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
