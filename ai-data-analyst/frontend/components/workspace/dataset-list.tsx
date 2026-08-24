import type { DatasetMetadata } from "@/lib/api";
import { formatNumber, formatTimestamp } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type DatasetListProps = {
  datasets: DatasetMetadata[];
  activeDatasetId: string | null;
  onSelect: (datasetId: string) => void;
  className?: string;
};

export function DatasetList({
  datasets,
  activeDatasetId,
  onSelect,
  className,
}: DatasetListProps) {
  if (datasets.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
        Recent datasets
      </p>

      <ul className="space-y-2">
        {datasets.map((dataset) => {
          const isActive = dataset.dataset_id === activeDatasetId;

          return (
            <li key={dataset.dataset_id}>
              <button
                type="button"
                onClick={() => onSelect(dataset.dataset_id)}
                aria-current={isActive ? "true" : undefined}
                className={cn(
                  "flex w-full flex-col gap-1 border px-3 py-3 text-left transition-colors duration-150",
                  isActive
                    ? "border-accent bg-accent-muted text-foreground shadow-[inset_2px_0_0_0_var(--accent)]"
                    : "border-border-subtle text-muted-strong hover:border-border hover:text-foreground",
                )}
              >
                <span className="truncate text-sm font-medium">
                  {dataset.original_filename}
                </span>
                <span
                  className={cn(
                    "font-mono text-[10px] tracking-widest uppercase",
                    isActive ? "text-accent" : "text-muted",
                  )}
                >
                  {formatNumber(dataset.profile.row_count)} rows ·{" "}
                  {formatTimestamp(dataset.created_at)}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
