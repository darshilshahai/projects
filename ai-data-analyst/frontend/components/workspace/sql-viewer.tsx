import { CopyButton } from "@/components/shared";
import { cn } from "@/lib/utils/cn";

type SqlViewerProps = {
  sql: string;
  className?: string;
};

export function SqlViewer({ sql, className }: SqlViewerProps) {
  return (
    <div className={cn("border border-border-subtle", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-border-subtle px-4 py-3">
        <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Executed query
        </p>
        <CopyButton value={sql} label="COPY SQL" />
      </div>
      <pre className="overflow-x-auto px-4 py-4 font-mono text-xs leading-relaxed text-muted-strong">
        <code>{sql}</code>
      </pre>
    </div>
  );
}
