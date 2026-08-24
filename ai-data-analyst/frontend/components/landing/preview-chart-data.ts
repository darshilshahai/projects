import type { ChartData } from "@/lib/api/chart-types";

export const PREVIEW_CHART_DATA: ChartData = {
  chart_type: "bar",
  title: "Total Revenue by Region",
  x: "region",
  y: "total_revenue",
  x_label: "Region",
  y_label: "Revenue",
  figure: {
    data: [
      {
        type: "bar",
        x: ["North", "West", "South"],
        y: [515000, 340000, 299000],
        marker: {
          color: "#b7ff17",
        },
        hovertemplate: "%{x}<br>%{y:,}<extra></extra>",
      },
    ],
    layout: {
      title: {
        text: "Total Revenue by Region",
      },
      xaxis: {
        title: {
          text: "Region",
        },
      },
      yaxis: {
        title: {
          text: "Revenue",
        },
      },
      margin: { l: 56, r: 24, t: 56, b: 48 },
    },
  },
};
