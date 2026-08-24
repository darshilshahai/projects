"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

const defaultGreetings = ["Hello", "नमस्ते", "Bonjour", "Ciao", "Olá", "こんにちは", "Hallo"];
const STORAGE_KEY = "portfolio-greeting-shown";

export function LaunchLoader({
  words = defaultGreetings,
  hold = 1540,
  home = false,
}: {
  words?: string[];
  hold?: number;
  home?: boolean;
}) {
  const reduceMotion = useReducedMotion();
  const [enabled, setEnabled] = useState(false);
  const [visible, setVisible] = useState(false);
  const [greeting, setGreeting] = useState(0);
  const activeWords = home ? defaultGreetings : words;

  useEffect(() => {
    if (!home) {
      setEnabled(true);
      setVisible(true);
      return;
    }

    if (window.sessionStorage.getItem(STORAGE_KEY) === "true") return;

    window.sessionStorage.setItem(STORAGE_KEY, "true");
    setEnabled(true);
    setVisible(true);
  }, [home]);

  useEffect(() => {
    if (!visible) return;

    if (reduceMotion) {
      setVisible(false);
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const greetingTimer =
      activeWords.length > 1
        ? window.setInterval(() => {
            setGreeting((current) => Math.min(current + 1, activeWords.length - 1));
          }, 205)
        : undefined;

    const exitTimer = window.setTimeout(() => setVisible(false), hold);

    return () => {
      if (greetingTimer) window.clearInterval(greetingTimer);
      window.clearTimeout(exitTimer);
      document.body.style.overflow = previousOverflow;
    };
  }, [activeWords.length, hold, reduceMotion, visible]);

  useEffect(() => {
    if (!visible && !enabled) document.body.style.overflow = "";
  }, [enabled, visible]);

  const handleExitComplete = () => {
    if (!visible) {
      setEnabled(false);
      document.body.style.overflow = "";
    }
  };

  if (!enabled) return null;

  return (
    <AnimatePresence onExitComplete={handleExitComplete}>
      {visible ? (
        <motion.div
          className="launch-loader"
          initial={{ y: 0, borderBottomLeftRadius: "0%", borderBottomRightRadius: "0%" }}
          exit={
            reduceMotion
              ? { opacity: 0 }
              : {
                  y: "-112%",
                  borderBottomLeftRadius: "52% 12%",
                  borderBottomRightRadius: "52% 12%",
                }
          }
          transition={{ duration: reduceMotion ? 0 : 0.78, ease: [0.76, 0, 0.24, 1] }}
          aria-label="Loading portfolio"
          role="status"
        >
          <div className="launch-greeting">
            <span aria-hidden="true">•</span>
            <AnimatePresence mode="popLayout" initial={false}>
              <motion.p
                key={activeWords[greeting]}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -7 }}
                transition={{ duration: 0.13, ease: "easeOut" }}
              >
                {activeWords[greeting]}
              </motion.p>
            </AnimatePresence>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
