"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { ColumnProfile } from "@/lib/api";
import { cn } from "@/lib/utils/cn";

type SchemaListProps = {
  columns: ColumnProfile[];
  className?: string;
};

export function SchemaList({ columns, className }: SchemaListProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={cn("border border-border-subtle", className)}>
      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors duration-150 hover:bg-background-panel/50"
      >
        <span className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Schema / {String(columns.length).padStart(2, "0")}
        </span>
        <ChevronDown
          className={cn(
            "size-3.5 text-muted transition-transform duration-150",
            expanded && "rotate-180 text-accent",
          )}
          aria-hidden="true"
        />
      </button>

      {expanded ? (
        <ul className="divide-y divide-border-subtle border-t border-border-subtle">
          {columns.map((column) => (
            <li
              key={column.name}
              className="flex items-baseline justify-between gap-3 px-4 py-3"
            >
              <div className="min-w-0">
                <p className="truncate text-sm text-foreground">{column.name}</p>
                {column.nullable ? (
                  <p className="mt-1 font-mono text-[10px] tracking-widest text-muted uppercase">
                    Nullable · {column.null_count} null
                    {column.null_count === 1 ? "" : "s"}
                  </p>
                ) : null}
              </div>
              <span className="shrink-0 font-mono text-[10px] tracking-widest text-muted uppercase">
                {column.duckdb_type}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
