"use client";

import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { site } from "@/data/site";
import { HeroStatus } from "@/components/layout/navbar";

const EASE = [0.22, 1, 0.36, 1] as const;

export function Hero() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="hero-signal" id="top" aria-label="Introduction">
      <div className="hero-signal-grid">
        <div className="hero-copy">
          <motion.p
            className="hero-eyebrow"
            initial={reduceMotion ? false : { y: 14 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.7, delay: 0.15, ease: EASE }}
          >
            {site.role} · {site.location} · Remote
          </motion.p>

          <motion.h1
            className="hero-title"
            initial={reduceMotion ? false : { y: 32 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.9, delay: 0.25, ease: EASE }}
          >
            Darshil
            <span>Shah</span>
          </motion.h1>

          <motion.p
            className="hero-lede"
            initial={reduceMotion ? false : { y: 18 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.75, delay: 0.4, ease: EASE }}
          >
            {site.headline}
          </motion.p>

          <motion.div
            className="hero-meta"
            initial={reduceMotion ? false : { y: 12 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.6, delay: 0.55, ease: EASE }}
          >
            <HeroStatus />
            <Link className="btn-signal btn-signal-sm" href="/work">
              View work
            </Link>
          </motion.div>
        </div>

        <motion.div
          className="hero-visual"
          initial={reduceMotion ? false : { x: 24 }}
          animate={{ x: 0 }}
          transition={{ duration: 1, delay: 0.3, ease: EASE }}
        >
          <div className="hero-frame">
            <img
              src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=900&q=88"
              alt="Portrait of Darshil Shah"
              fetchPriority="high"
              decoding="async"
            />
            <span className="hero-role-tag">{site.role}</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
