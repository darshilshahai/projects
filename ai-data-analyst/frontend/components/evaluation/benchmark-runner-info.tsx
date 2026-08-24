"use client";

import { CopyButton } from "@/components/shared";
import { TechnicalLabel } from "@/components/shared";

const CLI_COMMAND = "uv run python scripts/run_evaluation.py";

export function BenchmarkRunnerInfo() {
  return (
    <section className="space-y-4 border border-border-subtle p-5 md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <TechnicalLabel>RUN BENCHMARK</TechnicalLabel>
        <span className="font-mono text-[10px] tracking-[0.12em] text-warning uppercase">
          CLI only
        </span>
      </div>

      <pre className="overflow-x-auto border border-border-subtle bg-background px-4 py-4 font-mono text-xs leading-relaxed text-muted-strong">
        <code>{CLI_COMMAND}</code>
      </pre>

      <CopyButton value={CLI_COMMAND} label="COPY COMMAND" />

      <p className="text-sm leading-relaxed text-muted-strong">
        Benchmark execution currently runs from the backend CLI. API-triggered
        evaluation will be added later if needed.
      </p>
    </section>
  );
}
