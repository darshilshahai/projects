"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { magneticSpring, useMagnetic } from "@/hooks/use-magnetic";

type MagneticProps = {
  children: React.ReactNode;
  className?: string;
  strength?: number;
  innerStrength?: number;
};

export function Magnetic({
  children,
  className,
  strength = 18,
  innerStrength = 0.5,
}: MagneticProps) {
  const { offset, onPointerMove, onPointerLeave } = useMagnetic(strength);

  return (
    <motion.div
      className={className}
      animate={{ x: offset.x, y: offset.y }}
      transition={magneticSpring}
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
    >
      <motion.span
        animate={{ x: offset.x * innerStrength, y: offset.y * innerStrength }}
        transition={magneticSpring}
      >
        {children}
      </motion.span>
    </motion.div>
  );
}

type MagneticAnchorProps = MagneticProps & {
  href: string;
  ariaLabel?: string;
  external?: boolean;
};

export function MagneticAnchor({
  children,
  className,
  href,
  ariaLabel,
  external = false,
  strength = 20,
  innerStrength = 0.55,
}: MagneticAnchorProps) {
  const { offset, onPointerMove, onPointerLeave } = useMagnetic(strength);
  const motionProps = {
    className,
    "aria-label": ariaLabel,
    animate: { x: offset.x, y: offset.y },
    transition: magneticSpring,
    onPointerMove,
    onPointerLeave,
  };

  const inner = (
    <motion.span
      animate={{ x: offset.x * innerStrength, y: offset.y * innerStrength }}
      transition={magneticSpring}
    >
      {children}
    </motion.span>
  );

  if (external || href.startsWith("mailto:") || href.startsWith("http")) {
    return (
      <motion.a
        {...motionProps}
        href={href}
        target={external ? "_blank" : undefined}
        rel={external ? "noopener noreferrer" : undefined}
      >
        {inner}
      </motion.a>
    );
  }

  return (
    <MotionLink
      className={className}
      href={href}
      aria-label={ariaLabel}
      animate={{ x: offset.x, y: offset.y }}
      transition={magneticSpring}
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
    >
      {inner}
    </MotionLink>
  );
}

const MotionLink = motion.create(Link);

type MagneticButtonProps = MagneticProps & {
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
  ariaLabel?: string;
};

export function MagneticButton({
  children,
  className,
  type = "button",
  disabled,
  onClick,
  ariaLabel,
  strength = 22,
  innerStrength = 0.5,
}: MagneticButtonProps) {
  const { offset, onPointerMove, onPointerLeave } = useMagnetic(strength);

  return (
    <motion.button
      className={className}
      type={type}
      disabled={disabled}
      aria-label={ariaLabel}
      onClick={onClick}
      animate={{ x: offset.x, y: offset.y }}
      transition={magneticSpring}
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
    >
      <motion.span
        animate={{ x: offset.x * innerStrength, y: offset.y * innerStrength }}
        transition={magneticSpring}
      >
        {children}
      </motion.span>
    </motion.button>
  );
}
