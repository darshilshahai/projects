"use client";

import { motion, useReducedMotion } from "framer-motion";

type RevealProps = {
  children: React.ReactNode;
  as?: "div" | "article" | "p";
  className?: string;
  delay?: number;
};

// Scroll-triggered rise: opacity 0 / translateY(26px) → visible,
// matching the reference site's reveal treatment.
export function Reveal({
  children,
  as = "div",
  className,
  delay = 0,
}: RevealProps) {
  const reduceMotion = useReducedMotion();
  const Component =
    as === "article" ? motion.article : as === "p" ? motion.p : motion.div;

  return (
    <Component
      className={className}
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 26 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </Component>
  );
}
