"use client";

import { motion, useReducedMotion } from "framer-motion";
import { focusAreas, marqueeSkills } from "@/data/skills";

const EASE = [0.22, 1, 0.36, 1] as const;
const ticker = `${marqueeSkills.join("   /   ")}   /   `;

export function AiFocus() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="capabilities-section" id="skills">
      <div className="shell">
        <p className="section-tag">
          <em>04</em> — Capabilities
        </p>
        <h2 className="display" style={{ fontSize: "clamp(2.5rem, 5vw, 4rem)" }}>
          What I bring to a team.
        </h2>
        <div className="cap-grid">
          {focusAreas.map((area, i) => (
            <motion.article
              key={area.title}
              initial={reduceMotion ? {} : { opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: i * 0.06, ease: EASE }}
            >
              <span>{String(i + 1).padStart(2, "0")}</span>
              <h3>{area.title}</h3>
              <p>{area.description}</p>
            </motion.article>
          ))}
        </div>
      </div>
      <div className="skill-ticker" aria-hidden>
        <div className={reduceMotion ? undefined : "skill-ticker-track"}>
          <span>{ticker}</span>
          <span>{ticker}</span>
        </div>
      </div>
    </section>
  );
}
