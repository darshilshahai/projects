"use client";

import { useHabitStore } from "@/context/habit-store";

export function InspirationBanner() {
  const { inspiration, dataLoading } = useHabitStore();

  if (dataLoading && !inspiration) {
    return (
      <section className="mb-8 rounded-2xl border border-border/60 px-5 py-6 text-sm text-muted">
        Loading today’s focus…
      </section>
    );
  }

  if (!inspiration) {
    return null;
  }

  const { quote, author, manifestations } = inspiration;

  return (
    <section
      aria-label="Daily motivation"
      className="relative mb-8 overflow-hidden rounded-2xl border border-border/60"
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 90% 80% at 0% 0%, #1e3a5f66, transparent 55%), radial-gradient(ellipse 70% 60% at 100% 100%, #16161acc, transparent 50%), #121216",
        }}
      />
      <div className="relative px-5 py-5 sm:px-6 sm:py-6">
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted">
          Today&apos;s focus
        </p>
        <blockquote className="mt-3 max-w-2xl">
          <p className="text-base leading-relaxed text-foreground/95 sm:text-lg sm:leading-relaxed">
            “{quote}”
          </p>
          <footer className="mt-2 text-xs text-muted">— {author}</footer>
        </blockquote>
        <ul className="mt-5 flex flex-col gap-2 border-t border-border/50 pt-4 sm:flex-row sm:flex-wrap sm:gap-x-6 sm:gap-y-2">
          {manifestations.map((line) => (
            <li
              key={line}
              className="flex items-start gap-2 text-sm text-foreground/80"
            >
              <span
                className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                aria-hidden
              />
              <span>{line}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
