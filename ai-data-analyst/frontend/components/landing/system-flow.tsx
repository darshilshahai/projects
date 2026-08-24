"use client";

import { useState } from "react";
import { cn } from "@/lib/utils/cn";
import { SectionLabel } from "@/components/shared";
import { SECTION_IDS } from "@/lib/constants/site";
import { SectionReveal } from "./section-reveal";

const FLOW_STEPS = [
  {
    index: "01",
    title: "UPLOAD",
    description: "CSV enters an isolated dataset workspace.",
  },
  {
    index: "02",
    title: "INTERPRET",
    description: "The model understands the question and dataset schema.",
  },
  {
    index: "03",
    title: "VALIDATE",
    description: "Generated SQL passes through read-only validation.",
  },
  {
    index: "04",
    title: "EXECUTE",
    description: "DuckDB runs the approved query against the actual dataset.",
  },
  {
    index: "05",
    title: "EXPLAIN",
    description:
      "The computed result is returned with the exact SQL that produced it.",
  },
] as const;

export function SystemFlow() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  return (
    <SectionReveal>
      <section
        id={SECTION_IDS.howItWorks}
        className="scroll-mt-20 border-b border-border-subtle"
      >
        <div className="mx-auto max-w-7xl px-6 py-20 md:px-10 md:py-28">
          <SectionLabel index="02" trailing="ARCHITECTURE">
            HOW IT WORKS
          </SectionLabel>

          <div className="mt-10 overflow-x-auto pb-2">
            <div className="flex min-w-70 items-center gap-0">
              {FLOW_STEPS.map((step, index) => (
                <div key={step.index} className="flex flex-1 items-center">
                  <div
                    className={cn(
                      "flex h-10 flex-1 items-center justify-center border px-2 font-mono text-[10px] tracking-[0.12em] uppercase transition-colors duration-200",
                      activeIndex === index
                        ? "border-accent bg-accent-muted text-accent"
                        : "border-border-subtle text-muted",
                    )}
                  >
                    {step.title}
                  </div>
                  {index < FLOW_STEPS.length - 1 ? (
                    <div
                      className={cn(
                        "h-px w-6 shrink-0 transition-colors duration-200",
                        activeIndex !== null && index < activeIndex
                          ? "bg-accent"
                          : activeIndex === index
                            ? "bg-accent/60"
                            : "bg-border-subtle",
                      )}
                    />
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-12 divide-y divide-border-subtle border-y border-border-subtle">
            {FLOW_STEPS.map((step, index) => (
              <article
                key={step.index}
                className="grid gap-4 py-6 transition-colors duration-200 md:grid-cols-[120px_minmax(0,1fr)] md:gap-8"
                onMouseEnter={() => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
                onFocus={() => setActiveIndex(index)}
                onBlur={() => setActiveIndex(null)}
                tabIndex={0}
              >
                <div className="font-mono text-sm tracking-[0.08em] text-accent">
                  {step.index} / {step.title}
                </div>
                <p className="max-w-2xl text-sm leading-relaxed text-muted md:text-base">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </SectionReveal>
  );
}
