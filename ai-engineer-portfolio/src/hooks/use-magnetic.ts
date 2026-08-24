"use client";

import { useCallback, useState } from "react";
import { useReducedMotion } from "framer-motion";

export type MagneticOffset = { x: number; y: number };

const idle: MagneticOffset = { x: 0, y: 0 };

export const magneticSpring = {
  type: "spring" as const,
  stiffness: 240,
  damping: 20,
  mass: 0.45,
};

export function useMagnetic(strength = 16) {
  const reduceMotion = useReducedMotion();
  const [offset, setOffset] = useState<MagneticOffset>(idle);

  const onPointerMove = useCallback(
    (event: React.PointerEvent<HTMLElement>) => {
      if (reduceMotion || event.pointerType === "touch") return;
      const bounds = event.currentTarget.getBoundingClientRect();
      setOffset({
        x: ((event.clientX - bounds.left) / bounds.width - 0.5) * strength,
        y: ((event.clientY - bounds.top) / bounds.height - 0.5) * strength,
      });
    },
    [reduceMotion, strength],
  );

  const onPointerLeave = useCallback(() => setOffset(idle), []);

  return { offset, onPointerMove, onPointerLeave, reduceMotion };
}

export function setLiquidOrigin(event: React.PointerEvent<HTMLElement>) {
  const bounds = event.currentTarget.getBoundingClientRect();
  event.currentTarget.style.setProperty("--pill-x", `${event.clientX - bounds.left}px`);
  event.currentTarget.style.setProperty("--pill-y", `${event.clientY - bounds.top}px`);
}
