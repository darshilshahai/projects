"use client";

import dynamic from "next/dynamic";
import { motion, useReducedMotion } from "motion/react";
import { TechnicalLabel } from "@/components/shared";
import type { ChartData } from "@/lib/api";
import { mergeChartPresentationLayout } from "@/lib/utils/chart-theme";
import { cn } from "@/lib/utils/cn";
import type { Data, Layout } from "plotly.js";

const ChartPlot = dynamic(
  () =>
    import("@/components/shared/chart-plot").then((module) => module.ChartPlot),
  {
    ssr: false,
    loading: () => (
      <div className="flex min-h-70 items-center justify-center border border-border-subtle bg-background">
        <p className="font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
          Loading visualization
        </p>
      </div>
    ),
  },
);

type ChartViewProps = {
  chart: ChartData;
  className?: string;
};

function formatChartType(chartType: ChartData["chart_type"]): string {
  return chartType.toUpperCase();
}

export function ChartView({ chart, className }: ChartViewProps) {
  const prefersReducedMotion = useReducedMotion();

  const figureData = chart.figure.data as Data[];
  const presentationLayout = mergeChartPresentationLayout(
    chart.figure.layout as Partial<Layout> | undefined,
  );

  const content = (
    <div className={cn("space-y-3 border border-border-subtle", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-4 py-3">
        <TechnicalLabel tone="accent">
          VISUALIZATION / {formatChartType(chart.chart_type)}
        </TechnicalLabel>
      </div>

      <div className="px-4 pt-1">
        <h3 className="text-sm text-foreground">{chart.title}</h3>
      </div>

      <div className="px-2 pb-4">
        <ChartPlot data={figureData} layout={presentationLayout} />
      </div>
    </div>
  );

  if (prefersReducedMotion) {
    return content;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      {content}
    </motion.div>
  );
}

export function ChartErrorView({ className }: { className?: string }) {
  return (
    <div
      role="alert"
      className={cn(
        "space-y-2 border border-danger/30 bg-danger-muted px-4 py-4",
        className,
      )}
    >
      <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
        Visualization failed
      </p>
      <p className="text-sm text-muted-strong">
        The query ran successfully, but the result could not be visualized.
      </p>
    </div>
  );
}
