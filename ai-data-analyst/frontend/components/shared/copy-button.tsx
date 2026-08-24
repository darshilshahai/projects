"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils/cn";

type CopyButtonProps = {
  value: string;
  label?: string;
  className?: string;
};

export function CopyButton({
  value,
  label = "COPY",
  className,
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={cn(
        "inline-flex items-center gap-2 border border-border-subtle bg-transparent px-2.5 py-1.5 font-mono text-[10px] tracking-[0.14em] text-muted uppercase transition-colors duration-150 hover:border-border hover:text-foreground focus-visible:outline-none",
        copied && "border-accent/40 text-accent",
        className,
      )}
      aria-label={copied ? "Copied" : `Copy ${label.toLowerCase()}`}
    >
      {copied ? (
        <Check className="size-3" aria-hidden="true" />
      ) : (
        <Copy className="size-3" aria-hidden="true" />
      )}
      <span>{copied ? "COPIED" : label}</span>
    </button>
  );
}
