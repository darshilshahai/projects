"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { magneticSpring, setLiquidOrigin, useMagnetic } from "@/hooks/use-magnetic";
import { cn } from "@/lib/utils";

const MotionLink = motion.create(Link);

type LiquidPillProps = {
  href: string;
  children: React.ReactNode;
  className?: string;
  external?: boolean;
  strength?: number;
};

export function LiquidPill({ href, children, className, external = false, strength = 10 }: LiquidPillProps) {
  const { offset, onPointerMove, onPointerLeave } = useMagnetic(strength);
  const classNames = cn("btn-signal", className);

  const handleMove = (event: React.PointerEvent<HTMLElement>) => {
    setLiquidOrigin(event);
    onPointerMove(event);
  };

  const inner = (
    <motion.span animate={{ x: offset.x * 0.4, y: offset.y * 0.4 }} transition={magneticSpring}>
      {children}
    </motion.span>
  );

  if (external || href.startsWith("mailto:") || href.startsWith("http")) {
    return (
      <motion.a
        className={classNames}
        href={href}
        target={external ? "_blank" : undefined}
        rel={external ? "noopener noreferrer" : undefined}
        animate={{ x: offset.x, y: offset.y }}
        transition={magneticSpring}
        onPointerMove={handleMove}
        onPointerLeave={onPointerLeave}
      >
        {inner}
      </motion.a>
    );
  }

  return (
    <MotionLink
      className={classNames}
      href={href}
      animate={{ x: offset.x, y: offset.y }}
      transition={magneticSpring}
      onPointerMove={handleMove}
      onPointerLeave={onPointerLeave}
    >
      {inner}
    </MotionLink>
  );
}
