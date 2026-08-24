"use client";

import { TechnicalLabel } from "@/components/shared";
import { cn } from "@/lib/utils/cn";

export type StatusFilter = "all" | "passed" | "failed";
export type ActionFilter = "all" | "answer" | "chart" | "clarification";

type BenchmarkFiltersProps = {
  statusFilter: StatusFilter;
  actionFilter: ActionFilter;
  search: string;
  totalCount: number;
  onStatusFilterChange: (value: StatusFilter) => void;
  onActionFilterChange: (value: ActionFilter) => void;
  onSearchChange: (value: string) => void;
};

function FilterButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "border px-3 py-1.5 font-mono text-[10px] tracking-[0.12em] uppercase transition-colors duration-150",
        active
          ? "border-accent text-accent"
          : "border-border-subtle text-muted hover:border-border hover:text-foreground",
      )}
    >
      {label}
    </button>
  );
}

export function BenchmarkFilters({
  statusFilter,
  actionFilter,
  search,
  totalCount,
  onStatusFilterChange,
  onActionFilterChange,
  onSearchChange,
}: BenchmarkFiltersProps) {
  return (
    <div className="space-y-4 border-b border-border-subtle pb-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <TechnicalLabel tone="accent">BENCHMARK CASES / {totalCount}</TechnicalLabel>
        <input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search question..."
          className="w-full max-w-xs border border-border-subtle bg-background px-3 py-2 text-sm text-foreground outline-none placeholder:text-muted focus:border-accent sm:w-64"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterButton
          active={statusFilter === "all"}
          label="All"
          onClick={() => onStatusFilterChange("all")}
        />
        <FilterButton
          active={statusFilter === "passed"}
          label="Passed"
          onClick={() => onStatusFilterChange("passed")}
        />
        <FilterButton
          active={statusFilter === "failed"}
          label="Failed"
          onClick={() => onStatusFilterChange("failed")}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterButton
          active={actionFilter === "all"}
          label="All actions"
          onClick={() => onActionFilterChange("all")}
        />
        <FilterButton
          active={actionFilter === "answer"}
          label="Answer"
          onClick={() => onActionFilterChange("answer")}
        />
        <FilterButton
          active={actionFilter === "chart"}
          label="Chart"
          onClick={() => onActionFilterChange("chart")}
        />
        <FilterButton
          active={actionFilter === "clarification"}
          label="Clarification"
          onClick={() => onActionFilterChange("clarification")}
        />
      </div>
    </div>
  );
}
