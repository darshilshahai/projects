"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { LaunchLoader } from "@/components/layout/launch-loader";
import { Navbar } from "@/components/layout/navbar";
import { ContactBand } from "@/components/layout/contact-band";
import { experiences } from "@/data/experience";
import { focusAreas } from "@/data/skills";

const EASE = [0.22, 1, 0.36, 1] as const;

export function AboutView() {
  const reduceMotion = useReducedMotion();

  return (
    <main className="about-page" id="main">
      <LaunchLoader words={["About"]} hold={900} />
      <Navbar />

      <section className="about-page-hero shell">
        <motion.h1
          initial={reduceMotion ? {} : { opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.8, ease: EASE }}
        >
          Engineering discipline applied to AI products.
        </motion.h1>
        <div className="about-story">
          <motion.div
            initial={reduceMotion ? {} : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.75, delay: 1, ease: EASE }}
          >
            <p>
              I help teams turn complex AI ideas into clear, scalable products — with dependable
              architecture, thoughtful interaction, and measurable quality at every layer.
            </p>
            <p style={{ marginTop: 20 }}>
              Five years shipping backend systems, internal AI tools, and production RAG pipelines
              across insurance and enterprise software.
            </p>
          </motion.div>
          <motion.img
            src="https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=88"
            alt="Architectural interior with natural light"
            initial={reduceMotion ? {} : { clipPath: "inset(0 100% 0 0)" }}
            animate={{ clipPath: "inset(0 0% 0 0)" }}
            transition={{ duration: 1, delay: 1.1, ease: EASE }}
          />
        </div>
      </section>

      <section className="about-cap-block">
        <div className="shell">
          <p className="section-tag">
            <em>—</em> Services
          </p>
          <h2 className="display" style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>
            I can help you with
          </h2>
          <div className="cap-number-grid">
            {[
              {
                n: "01",
                t: "AI product engineering",
                c: "Reliable interfaces and production-grade foundations for AI-powered products.",
              },
              {
                n: "02",
                t: "RAG & agent systems",
                c: "Grounded retrieval, agentic workflows, evaluation, and observability.",
              },
              {
                n: "03",
                t: "Full-stack delivery",
                c: "From architecture and APIs to frontend — concept through deployment.",
              },
            ].map((item, i) => (
              <motion.article
                key={item.n}
                initial={reduceMotion ? {} : { opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.6, ease: EASE }}
              >
                <span>{item.n}</span>
                <h3>{item.t}</h3>
                <p style={{ color: "var(--muted)", lineHeight: 1.65 }}>{item.c}</p>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      <section className="shell" style={{ padding: "80px 0" }}>
        <p className="section-tag">
          <em>—</em> Background
        </p>
        <div style={{ marginTop: 32 }}>
          {experiences.map((exp) => (
            <article
              key={exp.company}
              style={{
                borderTop: "1px solid var(--line)",
                padding: "32px 0",
                display: "grid",
                gridTemplateColumns: "140px 1fr",
                gap: 32,
              }}
            >
              <span style={{ color: "var(--muted)", font: "12px var(--font-mono)" }}>{exp.period}</span>
              <div>
                <h3 style={{ margin: "0 0 6px", fontSize: "1.4rem" }}>{exp.company}</h3>
                <p style={{ color: "var(--signal)", margin: "0 0 12px", fontSize: 14 }}>{exp.role}</p>
                <p style={{ color: "var(--muted)", margin: 0, lineHeight: 1.65 }}>{exp.summary}</p>
              </div>
            </article>
          ))}
        </div>
        <div className="cap-grid" style={{ marginTop: 64 }}>
          {focusAreas.map((a, i) => (
            <article key={a.title}>
              <span>{String(i + 1).padStart(2, "0")}</span>
              <h3>{a.title}</h3>
              <p>{a.description}</p>
            </article>
          ))}
        </div>
        <p style={{ marginTop: 48 }}>
          <Link className="btn-signal" href="/contact">
            Get in touch →
          </Link>
        </p>
      </section>

      <ContactBand />
    </main>
  );
}
