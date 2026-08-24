import type { EvaluationSummary } from "@/lib/evaluation/types";
import {
  formatCurrencyUsd,
  formatLatencyMs,
  formatNumber,
} from "@/lib/utils/format";

type PerformanceStripProps = {
  summary: EvaluationSummary;
};

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-baseline gap-2">
      <span className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
        {label}
      </span>
      <span className="font-mono text-xs tracking-[0.04em] text-foreground tabular-nums">
        {value}
      </span>
    </span>
  );
}

export function PerformanceStrip({ summary }: PerformanceStripProps) {
  return (
    <section className="flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-border-subtle py-4">
      <Metric label="Avg latency" value={formatLatencyMs(summary.average_latency_ms)} />
      <span className="hidden text-muted sm:inline">/</span>
      <Metric label="P95 latency" value={formatLatencyMs(summary.p95_latency_ms)} />
      <span className="hidden text-muted sm:inline">/</span>
      <Metric label="Total tokens" value={formatNumber(summary.total_tokens)} />
      <span className="hidden text-muted sm:inline">/</span>
      <Metric
        label="Benchmark cost"
        value={formatCurrencyUsd(summary.total_estimated_cost_usd, 6)}
      />
      <span className="hidden text-muted sm:inline">/</span>
      <Metric
        label="Avg cost / case"
        value={formatCurrencyUsd(summary.average_cost_usd, 6)}
      />
    </section>
  );
}
