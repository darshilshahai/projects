"use client";

import { ChartView } from "@/components/workspace/chart-view";
import { PREVIEW_CHART_DATA } from "./preview-chart-data";

export function PreviewChart() {
  return <ChartView chart={PREVIEW_CHART_DATA} />;
}
