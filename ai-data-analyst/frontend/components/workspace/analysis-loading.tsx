"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils/cn";

const STAGES = [
  "INTERPRETING",
  "GENERATING QUERY",
  "VALIDATING",
  "EXECUTING",
  "VISUALIZING",
  "FORMATTING RESULT",
] as const;

export function AnalysisLoading({ className }: { className?: string }) {
  const prefersReducedMotion = useReducedMotion();
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    if (prefersReducedMotion) {
      return;
    }

    const interval = window.setInterval(() => {
      setStageIndex((current) => (current + 1) % STAGES.length);
    }, 900);

    return () => window.clearInterval(interval);
  }, [prefersReducedMotion]);

  const activeStage = STAGES[prefersReducedMotion ? STAGES.length - 1 : stageIndex];

  return (
    <div className={cn("space-y-4 border border-border-subtle p-5", className)}>
      <p className="font-mono text-[10px] tracking-[0.14em] text-accent uppercase animate-pulse">
        Analyzing
      </p>

      <div className="relative h-px overflow-hidden bg-border-subtle">
        {!prefersReducedMotion ? (
          <motion.div
            className="absolute inset-y-0 left-0 h-px w-1/3 bg-accent"
            animate={{ x: ["-100%", "400%"] }}
            transition={{
              duration: 1.4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ) : (
          <div className="h-px w-full bg-accent" />
        )}
      </div>

      <div className="space-y-2 font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
        {STAGES.map((stage, index) => {
          const isActive = stage === activeStage;
          const isPast =
            prefersReducedMotion || index < stageIndex;

          return (
            <p
              key={stage}
              className={cn(
                isActive && "text-accent",
                isPast && !isActive && "text-muted-strong",
              )}
            >
              {stage}
              {isActive ? " ↓" : isPast ? " ✓" : ""}
            </p>
          );
        })}
      </div>
    </div>
  );
}
