"use client";

import Link from "next/link";
import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import { site } from "@/data/site";

const EASE = [0.22, 1, 0.36, 1] as const;

export function Statement() {
  const ref = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();
  const inView = useInView(ref, { once: true, margin: "-10%" });

  const reveal = (delay: number) => ({
    initial: reduceMotion ? { opacity: 1 } : { opacity: 0, y: 32 },
    animate: inView ? { opacity: 1, y: 0 } : {},
    transition: { duration: 0.8, delay, ease: EASE },
  });

  return (
    <section className="statement" id="about" ref={ref}>
      <div className="shell">
        <p className="section-tag">
          <em>01</em> — Introduction
        </p>
        <div className="about-intro">
          <motion.h2 {...reveal(0)}>
            I build AI systems that survive contact with real users, real data, and real deadlines.
          </motion.h2>
          <div className="about-side">
            <motion.p {...reveal(0.1)}>{site.subheadline}</motion.p>
            <motion.div {...reveal(0.18)}>
              <Link className="btn-signal" href="/about">
                About me →
              </Link>
            </motion.div>
          </div>
        </div>
        <motion.div className="work-handoff" {...reveal(0.26)}>
          02 — Selected work
        </motion.div>
      </div>
    </section>
  );
}
