"use client";

import { motion, useReducedMotion } from "framer-motion";
import { experiences } from "@/data/experience";

const EASE = [0.22, 1, 0.36, 1] as const;

export function ExperienceSection() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="experience-section" id="experience">
      <div className="shell">
        <p className="section-tag">
          <em>03</em> — Experience
        </p>
        <h2>Built where failure has consequences.</h2>
        <div className="timeline">
          {experiences.map((exp, i) => (
            <motion.article
              key={exp.company}
              className="timeline-item"
              initial={reduceMotion ? {} : { opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-10%" }}
              transition={{ duration: 0.7, delay: i * 0.08, ease: EASE }}
            >
              <span>{exp.period}</span>
              <div>
                <h3>{exp.company}</h3>
                <p className="role">{exp.role}</p>
                <p>{exp.summary}</p>
                <p className="timeline-stack">{exp.stack.join(" · ")}</p>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
