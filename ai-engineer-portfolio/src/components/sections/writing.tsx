"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { articles } from "@/data/articles";

const EASE = [0.22, 1, 0.36, 1] as const;

export function WritingSection() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="writing-section" id="writing">
      <div className="shell">
        <div className="writing-header">
          <div>
            <p className="section-tag">
              <em>06</em> — Writing
            </p>
            <h2 className="display" style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>
              Field notes
            </h2>
          </div>
          <Link className="btn-signal" href="/writing">
            All notes
          </Link>
        </div>
        <div style={{ marginTop: 48 }}>
          {articles.slice(0, 3).map((article, i) => (
            <motion.div
              key={article.title}
              initial={reduceMotion ? {} : { opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.55, delay: i * 0.06, ease: EASE }}
            >
              {article.href ? (
                <Link className="note-row" href={article.href}>
                  <span>{article.category}</span>
                  <h3>{article.title}</h3>
                  <p>
                    {article.status} · {article.readingTime}
                  </p>
                </Link>
              ) : (
                <article className="note-row" style={{ opacity: 0.65 }}>
                  <span>{article.category}</span>
                  <h3>{article.title}</h3>
                  <p>
                    {article.status} · {article.readingTime}
                  </p>
                </article>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
