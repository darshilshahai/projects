import { TechnicalLabel } from "@/components/shared";
import type { ReportAnalysis } from "@/lib/evaluation/types";
import { formatNumber } from "@/lib/utils/format";

type SystemStatusProps = {
  analysis: ReportAnalysis;
  failedCases: number;
  totalCases: number;
};

export function SystemStatus({
  analysis,
  failedCases,
  totalCases,
}: SystemStatusProps) {
  return (
    <section className="space-y-4 border border-border-subtle p-5 md:p-6">
      <TechnicalLabel tone="danger">
        SYSTEM STATUS / {analysis.systemStatus}
      </TechnicalLabel>

      <div className="space-y-3">
        <p className="text-sm text-muted-strong">
          <span className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
            Primary issue:
          </span>{" "}
          {analysis.primaryIssue}
        </p>
        <p className="text-sm leading-relaxed text-foreground">
          {failedCases} / {formatNumber(totalCases)} cases failed overall.
        </p>
        <p className="text-sm leading-relaxed text-muted-strong">
          {analysis.statusMessage}
        </p>
      </div>

      <div className="border-t border-border-subtle pt-4">
        <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
          Evaluator note
        </p>
        <p className="mt-2 text-sm leading-relaxed text-muted-strong">
          Some failures may be evaluator mismatches rather than incorrect SQL.
        </p>
        {analysis.aliasMismatchExamples.length > 0 ? (
          <ul className="mt-3 space-y-2 font-mono text-[11px] text-muted-strong">
            {analysis.aliasMismatchExamples.map((example) => (
              <li key={example.id}>
                {example.id}: expected `{example.expected}` · actual `{example.actual}`
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}
