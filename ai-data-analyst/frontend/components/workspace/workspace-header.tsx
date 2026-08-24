import { StatusDot, TechnicalLabel } from "@/components/shared";
import type { DatasetMetadata } from "@/lib/api";
import { formatNumber } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type WorkspaceHeaderProps = {
  dataset: DatasetMetadata | null;
  engineOnline: boolean;
  className?: string;
};

export function WorkspaceHeader({
  dataset,
  engineOnline,
  className,
}: WorkspaceHeaderProps) {
  return (
    <header
      className={cn(
        "shrink-0 flex flex-col gap-3 border-b border-border-subtle px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6",
        className,
      )}
    >
      <div className="font-mono text-[10px] tracking-[0.12em] text-muted-strong uppercase">
        {dataset
          ? `${dataset.original_filename.toUpperCase()} / ${formatNumber(dataset.profile.row_count)} ROWS / ${formatNumber(dataset.profile.column_count)} COLUMNS`
          : "NO DATASET SELECTED"}
      </div>

      <div className="flex items-center gap-3">
        <StatusDot
          tone={engineOnline ? "online" : "offline"}
          label={engineOnline ? "ENGINE ONLINE" : "ENGINE OFFLINE"}
        />
        <TechnicalLabel tone="muted">DUCKDB</TechnicalLabel>
      </div>
    </header>
  );
}
