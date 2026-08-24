import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  FileSearch,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="hero-grid relative overflow-hidden px-6 pb-20 pt-16 lg:px-10 md:pb-28 md:pt-24">
      <div className="grid w-full gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div className="animate-fade-up">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary-soft px-4 py-1.5 text-sm font-medium text-primary">
            <Sparkles className="h-4 w-4" />
            RAG-powered fraud investigation
          </div>

          <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight text-foreground md:text-5xl md:leading-[1.08]">
            Investigate healthcare fraud with{" "}
            <span className="text-gradient">grounded answers</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-8 text-muted">
            Search investigation guidelines, claim records, and compliance
            documents semantically. Every answer is backed by retrieved evidence
            and source citations.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/sign-up">
              <Button size="lg" className="w-full sm:w-auto">
                Start investigating
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/sign-in">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Sign in to workspace
              </Button>
            </Link>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[
              { label: "Semantic search", value: "ChromaDB vectors" },
              { label: "Grounded answers", value: "Evidence-first LLM" },
              { label: "Live streaming", value: "SSE responses" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-border bg-card/70 px-4 py-3"
              >
                <p className="text-xs uppercase tracking-wide text-muted">
                  {item.label}
                </p>
                <p className="mt-1 text-sm font-medium text-foreground">
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="animate-fade-up [animation-delay:120ms]">
          <div className="rounded-[28px] border border-border bg-card p-6 shadow-[var(--shadow-lg)]">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">
                  Investigation preview
                </p>
                <p className="text-xs text-muted">Tenant: INSURER-001</p>
              </div>
              <span className="rounded-full bg-primary-soft px-3 py-1 text-xs font-medium text-primary">
                Live RAG
              </span>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl bg-muted-bg px-4 py-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted">
                  Question
                </p>
                <p className="mt-1 text-sm text-foreground">
                  What signs indicate duplicate billing fraud?
                </p>
              </div>

              <div className="rounded-2xl border border-primary/15 bg-primary-soft/50 px-4 py-4">
                <p className="text-xs font-medium uppercase tracking-wide text-primary">
                  Grounded answer
                </p>
                <p className="mt-2 text-sm leading-7 text-foreground">
                  Duplicate billing fraud may appear when the same medical service
                  is billed more than once. Compare invoice numbers, provider
                  names, treatment dates, and billed amounts. [Source 1]
                </p>
              </div>

              <div className="rounded-2xl border border-border px-4 py-3">
                <div className="flex items-center gap-2 text-xs text-muted">
                  <FileSearch className="h-4 w-4 text-primary" />
                  Retrieved from fraud-guidelines.pdf
                </div>
                <p className="mt-2 text-sm text-muted">
                  Score 0.68 · Chunk preview available in dashboard
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function FeaturesSection() {
  const features = [
    {
      icon: FileSearch,
      title: "Semantic document retrieval",
      description:
        "Find relevant fraud guidance even when investigators use different wording than the source documents.",
    },
    {
      icon: BookOpen,
      title: "Source-backed responses",
      description:
        "Answers include citations, chunk previews, and retrieval scores for audit-ready investigations.",
    },
    {
      icon: Zap,
      title: "Streaming investigations",
      description:
        "Watch answers stream in real time with latency metrics for retrieval and generation.",
    },
  ];

  return (
    <section id="features" className="px-6 py-20 lg:px-10">
      <div className="w-full">
        <div className="max-w-2xl">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
            Features
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
            Built for healthcare fraud teams
          </h2>
          <p className="mt-4 text-lg leading-8 text-muted">
            Ingest policies, claims, audit reports, and case notes. Ask natural
            language questions and receive evidence-grounded answers.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {features.map((feature) => (
            <article
              key={feature.title}
              className="rounded-[24px] border border-border bg-card p-6 shadow-[var(--shadow)] transition-transform duration-300 hover:-translate-y-1"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-soft text-primary">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-3 text-sm leading-7 text-muted">
                {feature.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function WorkflowSection() {
  const steps = [
    "Ingest healthcare fraud documents with tenant and category metadata.",
    "Chunk, embed, and store vectors in ChromaDB for semantic search.",
    "Ask investigation questions with optional filters.",
    "Review grounded answers, sources, and latency metrics.",
  ];

  return (
    <section id="workflow" className="bg-card px-6 py-20 lg:px-10">
      <div className="w-full">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
              Workflow
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              From documents to defensible answers
            </h2>
            <p className="mt-4 text-lg leading-8 text-muted">
              The same pipeline described in the project README: normalize,
              chunk, retrieve, generate, and cite.
            </p>
          </div>

          <div className="space-y-4">
            {steps.map((step, index) => (
              <div
                key={step}
                className="flex gap-4 rounded-2xl border border-border bg-background px-5 py-4"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-white">
                  {index + 1}
                </span>
                <p className="text-sm leading-7 text-foreground">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function SecuritySection() {
  return (
    <section id="security" className="px-6 py-20 lg:px-10">
      <div className="w-full rounded-[28px] border border-border bg-card px-8 py-10 shadow-[var(--shadow)] md:px-12">
        <div className="grid gap-8 md:grid-cols-[1fr_1.2fr] md:items-center">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
              Security
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Designed for sensitive healthcare data
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              "Tenant-scoped document search",
              "Category and metadata filters",
              "Evidence-only answer generation",
              "Latency and retrieval observability",
            ].map((item) => (
              <div
                key={item}
                className="rounded-2xl bg-primary-soft/60 px-4 py-3 text-sm font-medium text-foreground"
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function CtaSection() {
  return (
    <section className="px-6 pb-24 pt-4 lg:px-10">
      <div className="w-full rounded-[28px] bg-[linear-gradient(135deg,#0f766e_0%,#14b8a6_100%)] px-8 py-12 text-white shadow-[var(--shadow-lg)] md:px-12">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">
              Ready to investigate smarter?
            </h2>
            <p className="mt-3 max-w-xl text-base leading-7 text-white/80">
              Create a workspace and start asking fraud investigation questions
              against your document corpus.
            </p>
          </div>
          <Link href="/sign-up">
            <Button
              size="lg"
              className="bg-foreground text-primary hover:bg-foreground/90"
            >
              Create free workspace
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-card px-6 py-10 lg:px-10">
      <div className="flex w-full flex-col gap-4 text-sm text-muted md:flex-row md:items-center md:justify-between">
        <p>Veritas · Healthcare Fraud RAG Platform</p>
        <p>Built for semantic investigation workflows.</p>
      </div>
    </footer>
  );
}
