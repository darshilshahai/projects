import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type TechnicalLabelProps = {
  children: ReactNode;
  className?: string;
  tone?: "default" | "accent" | "danger" | "muted";
};

const toneClassName = {
  default: "text-muted-strong",
  accent: "text-accent",
  danger: "text-danger",
  muted: "text-muted",
} as const;

export function TechnicalLabel({
  children,
  className,
  tone = "default",
}: TechnicalLabelProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center font-mono text-[10px] tracking-[0.14em] uppercase",
        toneClassName[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
