"use client";

import { useState } from "react";
import type { AnalysisMetrics } from "@/lib/api";
import {
  formatCurrencyUsd,
  formatNumber,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type MetricsDetailsProps = {
  metrics: AnalysisMetrics;
  className?: string;
};

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
        {label}
      </dt>
      <dd className="font-mono text-xs tracking-[0.04em] text-foreground tabular-nums">
        {value}
      </dd>
    </div>
  );
}

export function MetricsDetails({ metrics, className }: MetricsDetailsProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={cn("space-y-3", className)}>
      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase transition-colors duration-150 hover:text-foreground"
        aria-expanded={expanded}
      >
        {expanded ? "DETAILS −" : "DETAILS +"}
      </button>

      {expanded ? (
        <dl className="space-y-2 border border-border-subtle p-4">
          <DetailRow
            label="Input tokens"
            value={formatNumber(metrics.input_tokens)}
          />
          <DetailRow
            label="Cached"
            value={formatNumber(metrics.cached_input_tokens)}
          />
          <DetailRow
            label="Output tokens"
            value={formatNumber(metrics.output_tokens)}
          />
          <DetailRow
            label="Reasoning tokens"
            value={formatNumber(metrics.reasoning_tokens)}
          />
          <DetailRow label="Total" value={formatNumber(metrics.total_tokens)} />
          <DetailRow
            label="Estimated cost"
            value={formatCurrencyUsd(metrics.estimated_cost_usd, 6)}
          />
        </dl>
      ) : null}
    </div>
  );
}
