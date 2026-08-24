import { SectionReveal } from "./section-reveal";

export function TrustSection() {
  return (
    <SectionReveal>
      <section className="border-b border-border-subtle">
        <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 md:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] md:px-10 md:py-28">
          <div className="space-y-2 md:pt-8">
            <h2 className="text-display text-[clamp(2.25rem,5vw,4.5rem)] text-foreground">
              The model doesn&apos;t calculate your answer.
            </h2>
            <p className="text-display text-[clamp(2.25rem,5vw,4.5rem)] text-accent">
              DuckDB does.
            </p>
          </div>

          <div className="max-w-md md:ml-auto md:pt-16">
            <p className="text-base leading-relaxed text-muted md:text-lg">
              The AI translates your question into a structured analytical action.
              Your backend validates it, executes it against the uploaded dataset,
              and returns the real result.
            </p>
          </div>
        </div>
      </section>
    </SectionReveal>
  );
}
