"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { GridBackground, StatusDot } from "@/components/shared";
import { SECTION_IDS, WORKSPACE_PATH } from "@/lib/constants/site";
import { PipelineVisual } from "./pipeline-visual";

const HEADLINE_LINES = [
  { id: "line-1", content: "Ask your data." },
  { id: "line-2", content: "See the" },
  {
    id: "line-3",
    content: (
      <>
        actual <span className="text-editorial text-accent">math.</span>
      </>
    ),
  },
] as const;

export function Hero() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <GridBackground fade className="min-h-[88vh] border-b border-border-subtle">
      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 py-16 md:gap-12 md:px-10 md:py-20">
        <div className="flex flex-col gap-3 font-mono text-[10px] tracking-[0.14em] text-muted uppercase sm:flex-row sm:items-center sm:justify-between">
          <span>QUERYMINT / 01</span>
          <span className="text-muted-strong">DUCKDB · OPENAI · REAL EXECUTION</span>
        </div>

        <div className="grid items-center gap-12 md:grid-cols-2 md:gap-10 lg:gap-16 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-8">
            <StatusDot tone="online" label="REAL COMPUTATION · NOT GUESSED ANSWERS" />

            <h1 className="space-y-1 md:space-y-2">
              {HEADLINE_LINES.map((line, index) => {
                const sharedClassName =
                  "block whitespace-nowrap text-display text-[clamp(2.25rem,5.5vw,5.75rem)] leading-[0.95] text-foreground";

                if (prefersReducedMotion) {
                  return (
                    <span key={line.id} className={sharedClassName}>
                      {line.content}
                    </span>
                  );
                }

                return (
                  <motion.span
                    key={line.id}
                    className={sharedClassName}
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      duration: 0.55,
                      delay: index * 0.06,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                  >
                    {line.content}
                  </motion.span>
                );
              })}
            </h1>

            <p className="max-w-[550px] text-base leading-relaxed text-muted md:text-lg">
              Upload a CSV, ask a question in plain English, and inspect the exact
              SQL executed against your real data.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <Link href={WORKSPACE_PATH} className="landing-cta landing-cta-primary">
                OPEN WORKSPACE ↘
              </Link>
              <a
                href={`#${SECTION_IDS.howItWorks}`}
                className="landing-cta landing-cta-secondary"
              >
                VIEW THE FLOW ↘
              </a>
            </div>
          </div>

          <div className="border border-border-subtle bg-background-panel/40 p-6 md:min-h-[420px] md:p-8">
            <PipelineVisual orientation="vertical" />
          </div>
        </div>
      </div>
    </GridBackground>
  );
}
