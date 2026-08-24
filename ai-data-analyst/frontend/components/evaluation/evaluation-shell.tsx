"use client";

import { motion, useReducedMotion } from "motion/react";
import type { EvaluationReport, ReportAnalysis } from "@/lib/evaluation/types";
import { BenchmarkRunnerInfo } from "./benchmark-runner-info";
import { BenchmarkTable } from "./benchmark-table";
import { EvaluationHeader } from "./evaluation-header";
import { EvaluationInsights } from "./evaluation-insights";
import { EvaluationScoreboard } from "./evaluation-scoreboard";
import { FailureBreakdown } from "./failure-breakdown";
import { LatencyView } from "./latency-view";
import { PerformanceStrip } from "./performance-strip";
import { ReportFiles } from "./report-files";
import { SystemStatus } from "./system-status";
import { TokenBreakdown } from "./token-breakdown";

type EvaluationShellProps = {
  report: EvaluationReport;
  analysis: ReportAnalysis;
};

const stagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.07 },
  },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] as const },
  },
};

function EvaluationSections({
  report,
  analysis,
}: EvaluationShellProps) {
  return (
    <div className="mx-auto max-w-7xl space-y-8 px-6 py-10 md:space-y-10 md:px-10 md:py-14">
      <EvaluationHeader summary={report.summary} />
      <EvaluationScoreboard summary={report.summary} />
      <SystemStatus
        analysis={analysis}
        failedCases={report.summary.failed_cases}
        totalCases={report.summary.total_cases}
      />
      <PerformanceStrip summary={report.summary} />
      <BenchmarkTable cases={report.cases} caseAnalyses={analysis.caseAnalyses} />
      <div className="grid gap-6 lg:grid-cols-2">
        <FailureBreakdown analysis={analysis} />
        <EvaluationInsights analysis={analysis} />
      </div>
      <LatencyView cases={report.cases} summary={report.summary} />
      <TokenBreakdown
        summary={report.summary}
        highestCostCases={analysis.highestCostCases}
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <BenchmarkRunnerInfo />
        <ReportFiles />
      </div>
    </div>
  );
}

export function EvaluationShell({ report, analysis }: EvaluationShellProps) {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return <EvaluationSections report={report} analysis={analysis} />;
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div variants={item}>
        <EvaluationSections report={report} analysis={analysis} />
      </motion.div>
    </motion.div>
  );
}
