import { cn } from "@/lib/utils/cn";

type StatusTone = "online" | "offline" | "busy" | "neutral";

type StatusDotProps = {
  tone?: StatusTone;
  pulse?: boolean;
  className?: string;
  label?: string;
};

const toneClassName: Record<StatusTone, string> = {
  online: "bg-accent shadow-[0_0_0_1px_rgba(183,255,23,0.25)]",
  offline: "bg-danger shadow-[0_0_0_1px_rgba(255,98,92,0.25)]",
  busy: "bg-accent/70",
  neutral: "bg-muted",
};

export function StatusDot({
  tone = "online",
  pulse = false,
  className,
  label,
}: StatusDotProps) {
  return (
    <span
      className={cn("inline-flex items-center gap-2", className)}
      role={label ? "status" : undefined}
      aria-label={label}
    >
      <span className="relative inline-flex size-1.5 shrink-0">
        {pulse ? (
          <span
            className={cn(
              "absolute inset-0 animate-ping rounded-full opacity-40",
              toneClassName[tone],
            )}
            aria-hidden="true"
          />
        ) : null}
        <span
          className={cn("relative size-1.5 rounded-full", toneClassName[tone])}
          aria-hidden="true"
        />
      </span>
      {label ? (
        <span className="font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
          {label}
        </span>
      ) : null}
    </span>
  );
}
