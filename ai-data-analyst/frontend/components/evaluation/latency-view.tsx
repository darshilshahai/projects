import { TechnicalLabel } from "@/components/shared";
import type { EvaluationCaseResult, EvaluationSummary } from "@/lib/evaluation/types";
import { formatLatencyMs } from "@/lib/utils/format";

type LatencyViewProps = {
  cases: EvaluationCaseResult[];
  summary: EvaluationSummary;
};

export function LatencyView({ cases, summary }: LatencyViewProps) {
  const maxLatency = Math.max(...cases.map((item) => item.latency_ms), 1);

  return (
    <section className="space-y-4 border border-border-subtle p-5 md:p-6">
      <TechnicalLabel>LATENCY BY CASE</TechnicalLabel>

      <div className="relative space-y-2">
        {cases.map((caseResult) => {
          const width = `${(caseResult.latency_ms / maxLatency) * 100}%`;

          return (
            <div key={caseResult.id} className="grid grid-cols-[48px_1fr_72px] items-center gap-3">
              <span className="font-mono text-[10px] text-muted uppercase">
                {caseResult.id}
              </span>
              <div className="relative h-3 bg-background-elevated">
                <div
                  className="h-full bg-accent/70"
                  style={{ width }}
                  title={formatLatencyMs(caseResult.latency_ms)}
                />
              </div>
              <span className="font-mono text-[10px] tabular-nums text-muted-strong">
                {formatLatencyMs(caseResult.latency_ms)}
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap gap-4 border-t border-border-subtle pt-4 font-mono text-[10px] tracking-[0.12em] uppercase text-muted">
        <span>Avg: {formatLatencyMs(summary.average_latency_ms)}</span>
        <span>P95: {formatLatencyMs(summary.p95_latency_ms)}</span>
      </div>
    </section>
  );
}
