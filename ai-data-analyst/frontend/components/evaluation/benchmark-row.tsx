"use client";

import { motion } from "motion/react";
import type { CaseAnalysis } from "@/lib/evaluation/types";
import {
  formatCurrencyUsd,
  formatLatencyMs,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";
import { CaseInspector } from "./case-inspector";

type BenchmarkRowProps = {
  analysis: CaseAnalysis;
  expanded: boolean;
  onToggle: () => void;
};

function PassFailCell({ passed }: { passed: boolean }) {
  return (
    <span
      className={cn(
        "font-mono text-[10px] tracking-[0.12em] uppercase",
        passed ? "text-accent" : "text-danger",
      )}
    >
      {passed ? "PASS" : "FAIL"}
    </span>
  );
}

function OptionalPassCell({
  applicable,
  passed,
}: {
  applicable: boolean;
  passed: boolean;
}) {
  if (!applicable) {
    return <span className="font-mono text-[10px] text-muted">—</span>;
  }

  return <PassFailCell passed={passed} />;
}

export function BenchmarkRow({ analysis, expanded, onToggle }: BenchmarkRowProps) {
  const { case: caseResult } = analysis;
  const valueApplicable =
    caseResult.expected_action === "answer" || caseResult.expected_action === "chart";
  const chartApplicable =
    caseResult.expected_action === "chart" || caseResult.actual_action === "chart";

  return (
    <>
      <tr
        className={cn(
          "cursor-pointer border-b border-border-subtle transition-colors duration-150 hover:bg-background-elevated",
          !caseResult.passed && "border-l-2 border-l-danger/60",
        )}
        onClick={onToggle}
      >
        <td className="px-3 py-3 font-mono text-xs text-foreground">{caseResult.id}</td>
        <td className="min-w-[220px] px-3 py-3 text-sm text-foreground">
          {caseResult.question}
        </td>
        <td className="px-3 py-3 font-mono text-[10px] uppercase text-muted-strong">
          {caseResult.expected_action}
        </td>
        <td className="px-3 py-3 font-mono text-[10px] uppercase text-muted-strong">
          {caseResult.actual_action}
        </td>
        <td className="px-3 py-3">
          <OptionalPassCell applicable={valueApplicable} passed={caseResult.values_pass} />
        </td>
        <td className="px-3 py-3">
          <OptionalPassCell applicable={chartApplicable} passed={caseResult.chart_pass} />
        </td>
        <td className="px-3 py-3 font-mono text-xs tabular-nums text-muted-strong">
          {formatLatencyMs(caseResult.latency_ms)}
        </td>
        <td className="px-3 py-3 font-mono text-xs tabular-nums text-muted-strong">
          {formatCurrencyUsd(caseResult.estimated_cost_usd, 4)}
        </td>
        <td className="px-3 py-3">
          <PassFailCell passed={caseResult.passed} />
        </td>
      </tr>

      {expanded ? (
        <tr className="border-b border-border-subtle">
          <td colSpan={9} className="p-0">
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              transition={{ duration: 0.2 }}
            >
              <CaseInspector analysis={analysis} />
            </motion.div>
          </td>
        </tr>
      ) : null}
    </>
  );
}

export function BenchmarkRowMobile({
  analysis,
  expanded,
  onToggle,
}: BenchmarkRowProps) {
  const { case: caseResult } = analysis;

  return (
    <div className="border-b border-border-subtle">
      <button
        type="button"
        onClick={onToggle}
        className="w-full space-y-2 px-3 py-4 text-left transition-colors duration-150 hover:bg-background-elevated"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="font-mono text-xs text-foreground">
            {caseResult.id} / {caseResult.passed ? "PASS" : "FAIL"}
          </span>
          <span className="font-mono text-[10px] text-muted uppercase">
            {expanded ? "Hide" : "Inspect"}
          </span>
        </div>
        <p className="text-sm text-foreground">{caseResult.question}</p>
        <div className="grid grid-cols-2 gap-2 font-mono text-[10px] uppercase text-muted-strong">
          <span>Expected: {caseResult.expected_action}</span>
          <span>Actual: {caseResult.actual_action}</span>
        </div>
        {caseResult.failure_reason ? (
          <p className="font-mono text-[10px] text-danger uppercase">
            {caseResult.failure_reason}
          </p>
        ) : null}
      </button>

      {expanded ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="px-3 pb-4"
        >
          <CaseInspector analysis={analysis} />
        </motion.div>
      ) : null}
    </div>
  );
}
