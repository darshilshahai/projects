import { TechnicalLabel } from "@/components/shared";
import type { EvaluationCaseResult, EvaluationSummary } from "@/lib/evaluation/types";
import {
  formatCurrencyUsd,
  formatNumber,
} from "@/lib/utils/format";

type TokenBreakdownProps = {
  summary: EvaluationSummary;
  highestCostCases: EvaluationCaseResult[];
};

export function TokenBreakdown({
  summary,
  highestCostCases,
}: TokenBreakdownProps) {
  return (
    <section className="grid gap-6 border border-border-subtle p-5 md:grid-cols-2 md:p-6">
      <div className="space-y-4">
        <TechnicalLabel>TOKEN BREAKDOWN</TechnicalLabel>
        <dl className="space-y-3 font-mono text-[11px] tracking-[0.08em] text-muted-strong">
          <div className="flex justify-between gap-4">
            <dt className="text-muted uppercase">Input</dt>
            <dd>{formatNumber(summary.total_input_tokens)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted uppercase">Output</dt>
            <dd>{formatNumber(summary.total_output_tokens)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted uppercase">Total</dt>
            <dd>{formatNumber(summary.total_tokens)}</dd>
          </div>
        </dl>
      </div>

      <div className="space-y-4">
        <TechnicalLabel tone="muted">MOST EXPENSIVE CASES</TechnicalLabel>
        <ul className="space-y-2">
          {highestCostCases.map((caseResult) => (
            <li
              key={caseResult.id}
              className="flex items-baseline justify-between gap-4 font-mono text-[11px]"
            >
              <span className="text-muted uppercase">{caseResult.id}</span>
              <span className="tabular-nums text-foreground">
                {formatCurrencyUsd(caseResult.estimated_cost_usd, 6)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
