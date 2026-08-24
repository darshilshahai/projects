"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils/cn";
import { TechnicalLabel } from "@/components/shared";

const STEPS = [
  { id: "01", label: "UPLOAD" },
  { id: "02", label: "UNDERSTAND" },
  { id: "03", label: "QUERY" },
  { id: "04", label: "EXECUTE" },
  { id: "05", label: "ANSWER" },
] as const;

const CYCLE_MS = 8000;
const STEP_MS = CYCLE_MS / STEPS.length;

function getStepStatus(stepIndex: number, activeIndex: number) {
  if (stepIndex < activeIndex) {
    return "done";
  }

  if (stepIndex === activeIndex) {
    return STEPS[stepIndex].label === "EXECUTE" ? "active" : "done";
  }

  return "pending";
}

type PipelineVisualProps = {
  className?: string;
  orientation?: "horizontal" | "vertical";
};

export function PipelineVisual({
  className,
  orientation = "vertical",
}: PipelineVisualProps) {
  const prefersReducedMotion = useReducedMotion();
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (prefersReducedMotion) {
      return;
    }

    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % STEPS.length);
    }, STEP_MS);

    return () => window.clearInterval(interval);
  }, [prefersReducedMotion]);

  const displayIndex = prefersReducedMotion ? STEPS.length - 1 : activeIndex;

  if (orientation === "vertical") {
    return (
      <div className={cn("flex h-full flex-col justify-center", className)}>
        <TechnicalLabel tone="muted" className="mb-6">
          ANALYSIS PIPELINE
        </TechnicalLabel>

        <div className="relative flex flex-col">
          {STEPS.map((step, index) => {
            const status = getStepStatus(index, displayIndex);
            const connectorFilled = index < displayIndex;
            const isLast = index === STEPS.length - 1;

            return (
              <div key={step.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "flex size-8 shrink-0 items-center justify-center border font-mono text-[10px] transition-colors duration-200",
                      status === "active"
                        ? "border-accent bg-accent-muted text-accent"
                        : status === "done"
                          ? "border-border text-accent"
                          : "border-border-subtle text-muted",
                    )}
                  >
                    {status === "done" ? "✓" : status === "active" ? "•" : step.id}
                  </div>
                  {!isLast ? (
                    <div className="relative my-1 w-px flex-1 min-h-8">
                      <div className="absolute inset-0 bg-border-subtle" />
                      {!prefersReducedMotion ? (
                        <motion.div
                          className="absolute inset-x-0 top-0 w-px origin-top bg-accent"
                          initial={false}
                          animate={{ scaleY: connectorFilled ? 1 : 0 }}
                          transition={{
                            duration: 0.35,
                            ease: [0.22, 1, 0.36, 1],
                          }}
                          style={{ height: "100%" }}
                        />
                      ) : (
                        <div
                          className={cn(
                            "absolute inset-x-0 top-0 h-full w-px bg-accent",
                            !connectorFilled && "opacity-0",
                          )}
                        />
                      )}
                    </div>
                  ) : null}
                </div>

                <div
                  className={cn(
                    "mb-4 flex min-h-8 flex-1 items-center border px-4 py-3 transition-colors duration-200",
                    status === "active"
                      ? "border-accent bg-accent-muted"
                      : status === "done"
                        ? "border-border"
                        : "border-border-subtle",
                  )}
                >
                  <div className="flex w-full items-center justify-between gap-3">
                    <span className="font-mono text-[11px] tracking-widest text-foreground uppercase">
                      {step.label}
                    </span>
                    <span
                      className={cn(
                        "font-mono text-[10px] tracking-[0.12em] text-muted",
                        (status === "done" || status === "active") && "text-accent",
                      )}
                    >
                      {status === "done"
                        ? "COMPLETE"
                        : status === "active"
                          ? "RUNNING"
                          : "WAITING"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <TechnicalLabel tone="muted">ANALYSIS PIPELINE</TechnicalLabel>

      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-70 items-start">
          {STEPS.map((step, index) => {
            const status = getStepStatus(index, displayIndex);
            const connectorFilled = index < displayIndex;

            return (
              <div key={step.id} className="flex flex-1 items-start">
                <div className="flex w-full flex-col items-start gap-2">
                  <div
                    className={cn(
                      "flex w-full flex-col gap-2 border px-3 py-3 transition-colors duration-200",
                      status === "active"
                        ? "border-accent bg-accent-muted"
                        : status === "done"
                          ? "border-border"
                          : "border-border-subtle",
                    )}
                  >
                    <span className="font-mono text-[10px] tracking-[0.12em] text-muted">
                      {step.id}
                    </span>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[11px] tracking-widest text-foreground uppercase">
                        {step.label}
                      </span>
                      <span
                        className={cn(
                          "font-mono text-[10px]",
                          status === "active"
                            ? "text-accent"
                            : status === "done"
                              ? "text-accent"
                              : "text-muted",
                        )}
                        aria-hidden="true"
                      >
                        {status === "done" ? "✓" : status === "active" ? "•" : ""}
                      </span>
                    </div>
                  </div>
                </div>

                {index < STEPS.length - 1 ? (
                  <div className="relative mt-6 h-px w-full min-w-6 flex-1 self-start">
                    <div className="absolute inset-0 bg-border-subtle" />
                    {!prefersReducedMotion ? (
                      <motion.div
                        className="absolute inset-y-0 left-0 origin-left bg-accent"
                        initial={false}
                        animate={{ scaleX: connectorFilled ? 1 : 0 }}
                        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                        style={{ width: "100%", height: "1px" }}
                      />
                    ) : (
                      <div
                        className={cn(
                          "absolute inset-y-0 left-0 h-px w-full bg-accent",
                          !connectorFilled && "opacity-0",
                        )}
                      />
                    )}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
