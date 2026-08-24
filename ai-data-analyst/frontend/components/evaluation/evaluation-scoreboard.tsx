import type { EvaluationSummary } from "@/lib/evaluation/types";
import { formatPercent } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type EvaluationScoreboardProps = {
  summary: EvaluationSummary;
};

type ScoreCellProps = {
  label: string;
  value: string;
  tone: "danger" | "warning" | "neutral" | "accent";
};

function ScoreCell({ label, value, tone }: ScoreCellProps) {
  const toneClass =
    tone === "danger"
      ? "text-danger"
      : tone === "warning"
        ? "text-warning"
        : tone === "accent"
          ? "text-accent"
          : "text-foreground";

  return (
    <div className="space-y-2 border-r border-border-subtle px-4 py-4 last:border-r-0 md:px-6">
      <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
        {label}
      </p>
      <p className={cn("font-mono text-2xl tracking-[-0.02em] tabular-nums", toneClass)}>
        {value}
      </p>
    </div>
  );
}

export function EvaluationScoreboard({ summary }: EvaluationScoreboardProps) {
  return (
    <section className="border border-border-subtle">
      <div className="grid grid-cols-2 md:grid-cols-4">
        <ScoreCell
          label="Pass rate"
          value={formatPercent(summary.pass_rate)}
          tone="warning"
        />
        <ScoreCell
          label="Action accuracy"
          value={formatPercent(summary.action_accuracy)}
          tone="neutral"
        />
        <ScoreCell
          label="Value accuracy"
          value={formatPercent(summary.value_accuracy)}
          tone="warning"
        />
        <ScoreCell
          label="Chart accuracy"
          value={formatPercent(summary.chart_accuracy)}
          tone="accent"
        />
      </div>
    </section>
  );
}
