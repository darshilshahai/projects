"use client";

import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import type { Data, Layout } from "plotly.js";

const Plot = createPlotlyComponent(Plotly);

type ChartPlotProps = {
  data: Data[];
  layout: Partial<Layout>;
  className?: string;
};

export function ChartPlot({ data, layout, className }: ChartPlotProps) {
  return (
    <div className={className}>
      <Plot
        data={data}
        layout={layout}
        config={{
          responsive: true,
          displaylogo: false,
          displayModeBar: false,
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
        className="min-h-70 w-full"
      />
    </div>
  );
}
