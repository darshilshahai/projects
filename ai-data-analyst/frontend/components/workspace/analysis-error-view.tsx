"use client";

import { useState } from "react";
import type { AnalysisState } from "@/hooks/use-analysis";
import { cn } from "@/lib/utils/cn";

type AnalysisErrorViewProps = {
  analysisState: Extract<AnalysisState, { status: "error" }>;
  className?: string;
};

export function AnalysisErrorView({
  analysisState,
  className,
}: AnalysisErrorViewProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isDev = process.env.NODE_ENV === "development";

  const title =
    analysisState.code === "sql_validation_error"
      ? "QUERY BLOCKED"
      : analysisState.code === "sql_execution_error"
        ? "QUERY BLOCKED"
        : analysisState.code === "chart_validation_error"
          ? "VISUALIZATION FAILED"
          : analysisState.code === "network_error"
            ? "ENGINE OFFLINE"
            : "ANALYSIS FAILED";

  const description =
    analysisState.code === "chart_validation_error"
      ? "The query ran successfully, but the result could not be visualized."
      : analysisState.code === "sql_validation_error" ||
          analysisState.code === "sql_execution_error"
        ? "The generated query did not pass the execution safety rules."
        : analysisState.message;

  return (
    <div
      role="alert"
      className={cn(
        "border border-danger/30 bg-danger-muted px-4 py-4 md:px-5",
        className,
      )}
    >
      <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
        {title}
      </p>
      <p className="mt-2 text-sm text-muted-strong">{description}</p>
      <p className="mt-3 font-mono text-[10px] tracking-widest text-muted uppercase">
        Question: {analysisState.question}
      </p>

      {isDev ? (
        <button
          type="button"
          onClick={() => setShowDetails((current) => !current)}
          className="mt-4 font-mono text-[10px] tracking-[0.12em] text-muted uppercase transition-colors duration-150 hover:text-foreground"
        >
          {showDetails ? "HIDE DETAILS" : "DETAILS"}
        </button>
      ) : null}

      {isDev && showDetails ? (
        <pre className="mt-3 overflow-x-auto border border-border-subtle bg-background px-3 py-3 font-mono text-[11px] leading-relaxed text-muted-strong">
          {JSON.stringify(
            { code: analysisState.code, message: analysisState.message },
            null,
            2,
          )}
        </pre>
      ) : null}
    </div>
  );
}
