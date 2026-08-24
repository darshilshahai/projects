"use client";

import { motion, useReducedMotion } from "motion/react";
import { FormattedAnswer, SectionLabel, StatusDot } from "@/components/shared";
import type { AnalysisAnswerResponse } from "@/lib/api";
import { AnalysisMetricsStrip } from "./analysis-metrics";
import { ChartView } from "./chart-view";
import { MetricsDetails } from "./metrics-details";
import { ResultTable } from "./result-table";
import { SqlViewer } from "./sql-viewer";

type AnswerViewProps = {
  result: AnalysisAnswerResponse;
  index: number;
};

const stagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 14 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] as const },
  },
};

function AnswerSections({
  result,
  index,
}: {
  result: AnalysisAnswerResponse;
  index: number;
}) {
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SectionLabel index={index}>ANALYSIS</SectionLabel>
        <StatusDot tone="online" label="EXECUTED" />
      </div>

      <p className="text-sm text-muted">{result.question}</p>

      <FormattedAnswer answer={result.answer} />

      {result.chart ? <ChartView chart={result.chart} /> : null}

      <div className="space-y-4">
        <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Result
        </p>
        <ResultTable
          columns={result.columns}
          rows={result.rows}
          rowCount={result.row_count}
        />
      </div>

      <div className="space-y-4">
        <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Query
        </p>
        <SqlViewer sql={result.sql} />
      </div>

      <AnalysisMetricsStrip metrics={result.metrics} />
      <MetricsDetails metrics={result.metrics} />
    </>
  );
}

export function AnswerView({ result, index }: AnswerViewProps) {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return (
      <article
        aria-live="polite"
        className="space-y-6 border border-border-subtle p-5 md:p-6"
      >
        <AnswerSections result={result} index={index} />
      </article>
    );
  }

  return (
    <motion.article
      aria-live="polite"
      className="space-y-6 border border-border-subtle p-5 md:p-6"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      <motion.div variants={item}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <SectionLabel index={index}>ANALYSIS</SectionLabel>
          <StatusDot tone="online" label="EXECUTED" />
        </div>
      </motion.div>

      <motion.p variants={item} className="text-sm text-muted">
        {result.question}
      </motion.p>

      <motion.div variants={item}>
        <FormattedAnswer answer={result.answer} />
      </motion.div>

      {result.chart ? (
        <motion.div variants={item}>
          <ChartView chart={result.chart} />
        </motion.div>
      ) : null}

      <motion.div variants={item} className="space-y-4">
        <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Result
        </p>
        <ResultTable
          columns={result.columns}
          rows={result.rows}
          rowCount={result.row_count}
        />
      </motion.div>

      <motion.div variants={item} className="space-y-4">
        <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Query
        </p>
        <SqlViewer sql={result.sql} />
      </motion.div>

      <motion.div variants={item}>
        <AnalysisMetricsStrip metrics={result.metrics} />
      </motion.div>

      <motion.div variants={item}>
        <MetricsDetails metrics={result.metrics} />
      </motion.div>
    </motion.article>
  );
}
