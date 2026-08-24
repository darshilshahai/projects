import { TechnicalLabel } from "@/components/shared";
import type { CaseAnalysis } from "@/lib/evaluation/types";
import { cn } from "@/lib/utils/cn";

type CaseInspectorProps = {
  analysis: CaseAnalysis;
  className?: string;
};

function StatusBadge({
  label,
  tone,
}: {
  label: string;
  tone: "pass" | "fail" | "neutral";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono text-[10px] tracking-[0.12em] uppercase",
        tone === "pass" && "text-accent",
        tone === "fail" && "text-danger",
        tone === "neutral" && "text-muted",
      )}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          tone === "pass" && "bg-accent",
          tone === "fail" && "bg-danger",
          tone === "neutral" && "bg-muted",
        )}
      />
      {label}
    </span>
  );
}

export function CaseInspector({ analysis, className }: CaseInspectorProps) {
  const { case: caseResult } = analysis;

  return (
    <div
      className={cn(
        "space-y-5 border border-border-subtle bg-background-elevated p-4 md:p-5",
        className,
      )}
    >
      <TechnicalLabel tone="accent">CASE / {caseResult.id}</TechnicalLabel>

      <div className="space-y-4">
        <div>
          <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
            Question
          </p>
          <p className="mt-2 text-sm leading-relaxed text-foreground">
            {caseResult.question}
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
              Expected action
            </p>
            <p className="mt-2 font-mono text-xs uppercase text-foreground">
              {caseResult.expected_action}
            </p>
          </div>
          <div>
            <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
              Actual action
            </p>
            <p className="mt-2 font-mono text-xs uppercase text-foreground">
              {caseResult.actual_action}
            </p>
          </div>
        </div>

        {caseResult.failure_reason ? (
          <div>
            <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
              Failure
            </p>
            <p className="mt-2 text-sm text-danger">{caseResult.failure_reason}</p>
          </div>
        ) : null}

        {caseResult.sql ? (
          <div>
            <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
              Executed SQL
            </p>
            <pre className="mt-2 overflow-x-auto border border-border-subtle bg-background px-3 py-3 font-mono text-xs leading-relaxed text-muted-strong">
              <code>{caseResult.sql}</code>
            </pre>
          </div>
        ) : null}

        <div className="space-y-3 border-t border-border-subtle pt-4">
          <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
            Likely diagnosis
          </p>

          {analysis.likelyCause ? (
            <p className="text-sm text-muted-strong">
              Likely cause:{" "}
              <span className="font-mono text-xs uppercase text-foreground">
                {analysis.likelyCause}
              </span>
            </p>
          ) : null}

          {analysis.queryLooksValid && !caseResult.values_pass ? (
            <StatusBadge label="Query looks valid" tone="neutral" />
          ) : null}

          {!caseResult.values_pass ? (
            <StatusBadge label="Benchmark value match failed" tone="fail" />
          ) : null}

          {analysis.expectedFields.length > 0 ? (
            <p className="font-mono text-[11px] text-muted-strong">
              Expected field: {analysis.expectedFields.join(", ")}
            </p>
          ) : null}

          {analysis.actualFields.length > 0 ? (
            <p className="font-mono text-[11px] text-muted-strong">
              Actual field: {analysis.actualFields.join(", ")}
            </p>
          ) : (
            <p className="font-mono text-[11px] text-muted-strong">
              Result row not stored in evaluation report.
            </p>
          )}

          {analysis.aliasMismatch ? (
            <p className="text-sm leading-relaxed text-warning">
              This may be an evaluator expectation mismatch rather than a
              calculation failure.
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
