import type { DatasetMetadata } from "@/lib/api";
import { formatBytes, formatNumber } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

export function DatasetSummary({
  dataset,
  onPreview,
  onDelete,
  className,
}: {
  dataset: DatasetMetadata;
  onPreview: () => void;
  onDelete: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "space-y-6 border border-accent/30 bg-accent-muted/20 p-4 shadow-[inset_2px_0_0_0_var(--accent)]",
        className,
      )}
    >
      <div>
        <p className="font-mono text-[10px] tracking-[0.14em] text-accent uppercase">
          Dataset / active
        </p>
        <p className="mt-3 truncate text-sm font-medium text-foreground">
          {dataset.original_filename}
        </p>
      </div>

      <dl className="space-y-2 font-mono text-[11px] tracking-[0.08em] text-muted-strong">
        <div className="flex justify-between gap-4">
          <dt className="text-muted uppercase">Rows</dt>
          <dd>{formatNumber(dataset.profile.row_count)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted uppercase">Columns</dt>
          <dd>{formatNumber(dataset.profile.column_count)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted uppercase">Size</dt>
          <dd>{formatBytes(dataset.size_bytes)}</dd>
        </div>
      </dl>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onPreview}
          className="landing-cta landing-cta-secondary"
        >
          PREVIEW
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="landing-cta border-danger/30 text-danger hover:border-danger hover:text-danger"
        >
          DELETE
        </button>
      </div>
    </div>
  );
}
