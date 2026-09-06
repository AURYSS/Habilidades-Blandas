import dynamic from "next/dynamic";
import type { PlotlyFigure } from "@/lib/types";

// Carga Plotly solo en el cliente para evitar SSR issues.
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotViewProps {
  figure: PlotlyFigure;
  className?: string;
  height?: number;
}

export function PlotView({ figure, className = "", height = 420 }: PlotViewProps) {
  const layout = {
    ...(figure.layout ?? {}),
    autosize: true,
    height,
    margin: { l: 48, r: 24, t: 48, b: 44, ...(figure.layout?.margin ?? {}) },
    font: { family: "Inter, system-ui, sans-serif", size: 12, color: "#334155" },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"] as never[],
  };

  return (
    <div className={`rounded-xl overflow-hidden ${className}`}>
      <Plot
        data={figure.data as never}
        layout={layout as never}
        config={config as never}
        useResizeHandler
        style={{ width: "100%", height }}
      />
    </div>
  );
}