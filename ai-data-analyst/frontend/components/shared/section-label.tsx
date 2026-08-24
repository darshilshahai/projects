import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type SectionLabelProps = {
  children: ReactNode;
  index?: string | number;
  className?: string;
  trailing?: ReactNode;
};

export function SectionLabel({
  children,
  index,
  className,
  trailing,
}: SectionLabelProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 font-mono text-[10px] tracking-[0.16em] text-muted uppercase",
        className,
      )}
    >
      <div className="flex min-w-0 items-center gap-3">
        {index !== undefined ? (
          <span className="shrink-0 text-accent">
            {typeof index === "number" ? String(index).padStart(2, "0") : index}
          </span>
        ) : null}
        <span className="truncate text-muted-strong">{children}</span>
      </div>
      {trailing ? <div className="shrink-0 text-muted">{trailing}</div> : null}
    </div>
  );
}
