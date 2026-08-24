"use client";

import type { AnalysisMetrics } from "@/lib/api";
import { SLOW_LATENCY_MS } from "@/lib/constants/metrics";
import {
  formatCurrencyUsd,
  formatLatencyMs,
  formatNumber,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type AnalysisMetricsStripProps = {
  metrics: AnalysisMetrics;
  className?: string;
};

type MetricItemProps = {
  label: string;
  value: string;
  valueClassName?: string;
};

function MetricItem({ label, value, valueClassName }: MetricItemProps) {
  return (
    <span className="inline-flex items-baseline gap-2">
      <span className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
        {label}
      </span>
      <span
        className={cn(
          "font-mono text-xs tracking-[0.04em] text-foreground tabular-nums",
          valueClassName,
        )}
      >
        {value}
      </span>
    </span>
  );
}

export function AnalysisMetricsStrip({
  metrics,
  className,
}: AnalysisMetricsStripProps) {
  const isSlow = metrics.latency_ms > SLOW_LATENCY_MS;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-border-subtle py-3",
        className,
      )}
    >
      <MetricItem
        label="Latency"
        value={formatLatencyMs(metrics.latency_ms)}
        valueClassName={isSlow ? "text-warning" : "text-accent"}
      />
      <span className="hidden text-muted sm:inline">/</span>
      <MetricItem
        label="Tokens"
        value={formatNumber(metrics.total_tokens)}
      />
      <span className="hidden text-muted sm:inline">/</span>
      <MetricItem
        label="LLM calls"
        value={formatNumber(metrics.llm_calls)}
      />
      <span className="hidden text-muted sm:inline">/</span>
      <MetricItem
        label="Cost"
        value={formatCurrencyUsd(metrics.estimated_cost_usd)}
        valueClassName="text-accent"
      />
    </div>
  );
}
