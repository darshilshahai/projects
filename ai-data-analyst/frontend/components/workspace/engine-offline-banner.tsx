import { StatusDot } from "@/components/shared";
import { cn } from "@/lib/utils/cn";

type EngineOfflineBannerProps = {
  className?: string;
};

export function EngineOfflineBanner({ className }: EngineOfflineBannerProps) {
  return (
    <div
      role="alert"
      className={cn(
        "shrink-0 border-b border-danger/30 bg-danger-muted px-4 py-3 md:px-6",
        className,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] tracking-[0.14em] text-danger uppercase">
            Engine offline
          </p>
          <p className="mt-1 text-sm text-muted-strong">
            Cannot reach the analysis API. Start the backend and refresh this page.
          </p>
        </div>
        <StatusDot tone="offline" label="OFFLINE" />
      </div>
    </div>
  );
}
