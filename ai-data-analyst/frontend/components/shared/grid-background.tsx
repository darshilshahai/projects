import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type GridBackgroundProps = {
  className?: string;
  fade?: boolean;
  children?: ReactNode;
};

export function GridBackground({
  className,
  fade = false,
  children,
}: GridBackgroundProps) {
  return (
    <div className={cn("relative isolate overflow-hidden", className)}>
      <div
        aria-hidden="true"
        className={cn(
          "pointer-events-none absolute inset-0 bg-grid",
          fade && "bg-grid-fade",
        )}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
