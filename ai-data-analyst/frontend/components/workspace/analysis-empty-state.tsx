import { cn } from "@/lib/utils/cn";

type AnalysisEmptyStateProps = {
  datasetName?: string;
  className?: string;
};

export function AnalysisEmptyState({
  datasetName,
  className,
}: AnalysisEmptyStateProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
        Analysis / ready
      </p>
      <h2 className="text-display text-3xl text-foreground md:text-4xl">
        Ask your data.
      </h2>
      <p className="max-w-xl text-sm leading-relaxed text-muted md:text-base">
        {datasetName
          ? `${datasetName} is loaded. Submit a question below to run validated DuckDB SQL against your dataset.`
          : "Select a dataset from the sidebar to continue."}
      </p>
      <div className="border border-dashed border-border-subtle px-4 py-4">
        <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
          Trust the computation
        </p>
        <p className="mt-2 text-sm text-muted-strong">
          Every answer includes the exact SQL executed against your uploaded CSV.
        </p>
      </div>
    </div>
  );
}
