import { SectionLabel, TechnicalLabel } from "@/components/shared";
import { SECTION_IDS } from "@/lib/constants/site";
import { SectionReveal } from "./section-reveal";

const PROOF_MODULES = [
  {
    title: "REAL EXECUTION",
    description: "Numbers come from DuckDB, not language-model arithmetic.",
    metadata: [
      { label: "MODE", value: "READ_ONLY" },
      { label: "ENGINE", value: "DUCKDB" },
    ],
  },
  {
    title: "VISIBLE SQL",
    description: "Every result includes the exact query that ran.",
    metadata: [
      { label: "OUTPUT", value: "SQL + ROWS" },
      { label: "SOURCE", value: "BACKEND" },
    ],
  },
  {
    title: "AMBIGUITY CONTROL",
    description:
      "Undefined requests trigger clarification instead of assumptions.",
    metadata: [
      { label: "POLICY", value: "ASK_FIRST" },
      { label: "DEFAULT", value: "NONE" },
    ],
  },
  {
    title: "DATA BOUNDARY",
    description: "Only the uploaded dataset is exposed to the analysis engine.",
    metadata: [
      { label: "TABLES", value: "DATASET / ONLY" },
      { label: "ROW LIMIT", value: "200" },
    ],
  },
] as const;

export function ProofSection() {
  return (
    <SectionReveal>
      <section
        id={SECTION_IDS.product}
        className="scroll-mt-20 border-b border-border-subtle"
      >
        <div className="mx-auto max-w-7xl px-6 py-20 md:px-10 md:py-28">
          <SectionLabel index="03" trailing="SYSTEM EVIDENCE">
            BUILT FOR VERIFIABILITY
          </SectionLabel>

          <div className="mt-10 grid gap-px border border-border-subtle bg-border-subtle md:grid-cols-2 xl:grid-cols-4">
            {PROOF_MODULES.map((module) => (
              <article
                key={module.title}
                className="flex min-h-56 flex-col justify-between bg-background p-6"
              >
                <div className="space-y-4">
                  <h3 className="font-mono text-[11px] tracking-[0.12em] text-foreground uppercase">
                    {module.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-muted">
                    {module.description}
                  </p>
                </div>

                <dl className="mt-8 space-y-2 border-t border-border-subtle pt-4">
                  {module.metadata.map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center justify-between gap-4"
                    >
                      <TechnicalLabel tone="muted">{item.label}</TechnicalLabel>
                      <dd className="font-mono text-[10px] tracking-widest text-muted-strong uppercase">
                        {item.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              </article>
            ))}
          </div>
        </div>
      </section>
    </SectionReveal>
  );
}
