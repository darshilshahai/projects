"use client";

import { motion, useReducedMotion } from "framer-motion";
import { articles } from "@/data/articles";
import { LaunchLoader } from "@/components/layout/launch-loader";
import { Navbar } from "@/components/layout/navbar";
import { ContactBand } from "@/components/layout/contact-band";

export function WritingView() {
  const reduceMotion = useReducedMotion();

  return (
    <main className="writing-page" id="main">
      <LaunchLoader words={["Notes"]} hold={850} />
      <Navbar />

      <div className="shell writing-page-shell">
        <motion.h1
          className="display"
          style={{ fontSize: "clamp(2.5rem, 5vw, 4rem)" }}
          initial={reduceMotion ? {} : { opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.85, delay: 0.75 }}
        >
          Notes from the field
        </motion.h1>
        <p className="writing-lede">
          Practical writing on RAG, agents, streaming APIs, and evaluation. Drafts become links when published.
        </p>
        <div className="writing-archive">
          {articles.map((article, i) => (
            <motion.article
              key={article.title}
              className="note-row"
              style={{ opacity: article.href ? 1 : 0.6 }}
              initial={reduceMotion ? {} : { opacity: 0, y: 16 }}
              animate={{ opacity: article.href ? 1 : 0.6, y: 0 }}
              transition={{ delay: 0.9 + i * 0.06, duration: 0.55 }}
            >
              <span>{article.category}</span>
              <h3>{article.title}</h3>
              <p>
                {article.status} · {article.year} · {article.readingTime}
              </p>
            </motion.article>
          ))}
        </div>
      </div>

      <ContactBand />
    </main>
  );
}
