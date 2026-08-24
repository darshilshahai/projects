import { SectionLabel } from "@/components/shared";
import type { EvaluationSummary } from "@/lib/evaluation/types";
import { formatNumber } from "@/lib/utils/format";

type EvaluationHeaderProps = {
  summary: EvaluationSummary;
};

export function EvaluationHeader({ summary }: EvaluationHeaderProps) {
  return (
    <section className="grid gap-8 border-b border-border-subtle pb-10 md:grid-cols-[1.2fr_0.8fr] md:items-end">
      <div className="space-y-5">
        <SectionLabel index="01">SYSTEM EVALUATION</SectionLabel>
        <h1 className="text-display text-[clamp(2rem,4.5vw,3.75rem)] leading-[0.95] text-foreground">
          Measure the system,
          <br />
          not the demo.
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-strong md:text-base">
          A fixed benchmark checks tool selection, computed values, chart choice,
          latency, token usage, and estimated cost.
        </p>
      </div>

      <dl className="grid grid-cols-2 gap-4 border border-border-subtle p-4 font-mono text-[10px] tracking-[0.12em] uppercase">
        <div>
          <dt className="text-muted">Last run</dt>
          <dd className="mt-2 text-foreground">{formatNumber(summary.total_cases)} cases</dd>
        </div>
        <div>
          <dt className="text-muted">Passed</dt>
          <dd className="mt-2 text-muted-strong">{formatNumber(summary.passed_cases)}</dd>
        </div>
        <div>
          <dt className="text-muted">Failed</dt>
          <dd className="mt-2 text-danger">{formatNumber(summary.failed_cases)}</dd>
        </div>
        <div>
          <dt className="text-muted">Pass rate</dt>
          <dd className="mt-2 text-warning">{summary.pass_rate.toFixed(2)}%</dd>
        </div>
      </dl>
    </section>
  );
}
