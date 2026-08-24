import { TechnicalLabel } from "@/components/shared";
import type { ReportAnalysis } from "@/lib/evaluation/types";

type EvaluationInsightsProps = {
  analysis: ReportAnalysis;
};

export function EvaluationInsights({ analysis }: EvaluationInsightsProps) {
  return (
    <section className="space-y-4 border border-border-subtle p-5 md:p-6">
      <TechnicalLabel>WHAT THE RUN TELLS US</TechnicalLabel>
      <ol className="space-y-4">
        {analysis.insights.map((insight, index) => (
          <li key={insight} className="flex gap-4">
            <span className="font-mono text-[10px] tracking-[0.12em] text-accent">
              {String(index + 1).padStart(2, "0")}
            </span>
            <p className="text-sm leading-relaxed text-muted-strong">{insight}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
