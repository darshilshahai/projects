import { TechnicalLabel } from "@/components/shared";
import type { ReportAnalysis } from "@/lib/evaluation/types";

type FailureBreakdownProps = {
  analysis: ReportAnalysis;
};

function FailureGroup({
  label,
  caseIds,
}: {
  label: string;
  caseIds: string[];
}) {
  return (
    <div className="space-y-2 border-t border-border-subtle pt-4 first:border-t-0 first:pt-0">
      <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
        {label}
      </p>
      <p className="font-mono text-xs text-foreground">
        {caseIds.length > 0 ? caseIds.join(", ") : "none"}
      </p>
    </div>
  );
}

export function FailureBreakdown({ analysis }: FailureBreakdownProps) {
  return (
    <section className="space-y-4 border border-border-subtle p-5 md:p-6">
      <TechnicalLabel>FAILURE BREAKDOWN</TechnicalLabel>

      <FailureGroup
        label="Action mismatch"
        caseIds={analysis.failureBreakdown["ACTION MISMATCH"].map((item) => item.id)}
      />
      <FailureGroup
        label="Value mismatch"
        caseIds={analysis.failureBreakdown["VALUE MISMATCH"].map((item) => item.id)}
      />
      <FailureGroup
        label="Chart mismatch"
        caseIds={analysis.failureBreakdown["CHART MISMATCH"].map((item) => item.id)}
      />
      <FailureGroup
        label="Execution error"
        caseIds={analysis.failureBreakdown["EXECUTION ERROR"].map((item) => item.id)}
      />
    </section>
  );
}
