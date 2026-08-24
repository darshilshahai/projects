"use client";

import { useState } from "react";
import type { AnalysisClarificationResponse, ClarificationOption } from "@/lib/api";
import { isCustomClarificationOption } from "@/lib/utils/clarification";
import { cn } from "@/lib/utils/cn";
import { AnalysisMetricsStrip } from "./analysis-metrics";
import { MetricsDetails } from "./metrics-details";

type ClarificationViewProps = {
  result: AnalysisClarificationResponse;
  onSubmit: (value: string) => void;
  loading?: boolean;
  className?: string;
};

export function ClarificationView({
  result,
  onSubmit,
  loading = false,
  className,
}: ClarificationViewProps) {
  const [selectedOption, setSelectedOption] = useState<ClarificationOption | null>(
    null,
  );
  const [customAnswer, setCustomAnswer] = useState("");

  const showCustomInput =
    selectedOption !== null && isCustomClarificationOption(selectedOption.value);

  function handleOptionClick(option: ClarificationOption) {
    if (loading) {
      return;
    }

    if (isCustomClarificationOption(option.value)) {
      setSelectedOption(option);
      return;
    }

    onSubmit(option.value);
  }

  function handleCustomSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!customAnswer.trim() || loading) {
      return;
    }

    onSubmit(customAnswer.trim());
  }

  return (
    <div className={cn("space-y-5 border border-border-subtle p-5 md:p-6", className)}>
      <p className="font-mono text-[10px] tracking-[0.14em] text-accent uppercase">
        Clarification required
      </p>

      <p className="text-sm text-muted">{result.question}</p>

      <p className="text-base leading-relaxed text-foreground">
        {result.clarification_question}
      </p>

      <div className="space-y-3">
        <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          Choose one
        </p>

        <div className="grid gap-2 sm:grid-cols-2">
          {result.options.map((option) => {
            const isSelected = selectedOption?.value === option.value;
            const isCustom = isCustomClarificationOption(option.value);

            return (
              <button
                key={`${option.label}-${option.value}`}
                type="button"
                disabled={loading}
                onClick={() => handleOptionClick(option)}
                className={cn(
                  "border px-4 py-3 text-left transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50",
                  isSelected
                    ? "border-accent bg-accent-muted text-foreground"
                    : "border-border-subtle text-muted-strong hover:border-border hover:text-foreground",
                  !isCustom && "hover:border-accent/40",
                )}
              >
                <span className="block text-sm font-medium">{option.label}</span>
                {!isCustom ? (
                  <span className="mt-1 block font-mono text-[10px] tracking-widest text-muted uppercase">
                    {option.value}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      </div>

      {showCustomInput ? (
        <form onSubmit={handleCustomSubmit} className="space-y-3 border-t border-border-subtle pt-4">
          <label className="block space-y-2">
            <span className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
              Specify your metric
            </span>
            <input
              type="text"
              value={customAnswer}
              onChange={(event) => setCustomAnswer(event.target.value)}
              placeholder="e.g. profit margin"
              disabled={loading}
              autoFocus
              className="w-full border border-border-subtle bg-background px-3 py-3 text-sm text-foreground outline-none transition-colors duration-150 placeholder:text-muted focus:border-accent"
            />
          </label>

          <button
            type="submit"
            disabled={loading || !customAnswer.trim()}
            className="landing-cta landing-cta-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "ANALYZING..." : "SUBMIT CLARIFICATION ↗"}
          </button>
        </form>
      ) : null}

      <AnalysisMetricsStrip metrics={result.metrics} />
      <MetricsDetails metrics={result.metrics} />
    </div>
  );
}
