"use client";

import { motion, useReducedMotion } from "framer-motion";

const nodes = [
  { index: "01", label: "Query" },
  { index: "02", label: "Retrieve" },
  { index: "03", label: "Context" },
  { index: "04", label: "Reason" },
  { index: "05", label: "Response" },
];

const BASE = 1.15;
const STEP = 0.38;

// "Live system map": nodes activate in order, connectors draw with a
// travelling pulse, checkmarks pop, and the progress bar tracks the run.
export function HeroPipeline() {
  const reduceMotion = useReducedMotion();

  return (
    <>
      <div className="pipeline-label">
        <span>LIVE SYSTEM MAP</span>
        <span className="system-state">
          <i /> PROCESS COMPLETE
        </span>
        <span>RAG / 01</span>
      </div>

      <div className="pipeline">
        {nodes.map((node, index) => {
          const isLast = index === nodes.length - 1;
          return (
            <div className="pipe-unit" key={node.index}>
              <motion.div
                className="pipe-node"
                initial={
                  reduceMotion
                    ? { opacity: 0 }
                    : { opacity: 0, scale: 0.9 }
                }
                animate={{ opacity: 1, scale: 1 }}
                transition={{
                  duration: 0.35,
                  delay: BASE + index * STEP,
                  ease: "easeOut",
                }}
              >
                {node.index}
                <b>{node.label}</b>
                <motion.i
                  className="node-check"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{
                    duration: 0.25,
                    delay: BASE + 0.45 + index * STEP,
                    ease: "easeOut",
                  }}
                >
                  ✓
                </motion.i>
              </motion.div>
              {!isLast ? (
                <motion.span
                  className="pipe-line"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{
                    duration: 0.3,
                    delay: BASE + 0.2 + index * STEP,
                    ease: "easeOut",
                  }}
                >
                  <i
                    style={
                      reduceMotion
                        ? undefined
                        : {
                            animation: `dotTravel 0.85s ease-in-out ${
                              BASE + 0.25 + index * STEP
                            }s forwards`,
                          }
                    }
                  />
                </motion.span>
              ) : null}
            </div>
          );
        })}
      </div>

      <motion.div
        className="hero-progress"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1.9, delay: BASE, ease: "easeInOut" }}
      />
    </>
  );
}
