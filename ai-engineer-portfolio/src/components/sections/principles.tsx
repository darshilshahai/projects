"use client";

import { motion, useReducedMotion } from "framer-motion";
import { principles } from "@/data/skills";

const EASE = [0.22, 1, 0.36, 1] as const;

export function Principles() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="principles-section" aria-labelledby="principles-heading">
      <div className="shell">
        <p className="section-tag" id="principles-heading">
          <em>05</em> — Principles
        </p>
        {principles.map((principle, i) => (
          <motion.div
            key={principle}
            className="principle-row"
            initial={reduceMotion ? {} : { opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: i * 0.05, ease: EASE }}
          >
            <span>{String(i + 1).padStart(2, "0")}</span>
            <p>{principle}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
