import Link from "next/link";
import { WORKSPACE_PATH } from "@/lib/constants/site";
import { SectionReveal } from "./section-reveal";

export function FinalCta() {
  return (
    <SectionReveal>
      <section>
        <div className="mx-auto flex max-w-7xl flex-col items-start gap-8 px-6 py-24 md:px-10 md:py-32">
          <h2 className="text-display max-w-3xl text-[clamp(2.5rem,6vw,5rem)] text-foreground">
            Bring a CSV.
            <br />
            Leave with evidence.
          </h2>

          <Link href={WORKSPACE_PATH} className="landing-cta landing-cta-primary">
            ANALYZE A DATASET ↘
          </Link>

          <p className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
            CSV · DUCKDB · OPENAI
          </p>
        </div>
      </section>
    </SectionReveal>
  );
}
