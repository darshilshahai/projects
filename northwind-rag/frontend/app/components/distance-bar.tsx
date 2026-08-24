import { DISTANCE_SCALE_MAX, DISTANCE_THRESHOLD } from "../lib/constants";

interface Tier {
  label: string;
  fill: string;
  textClass: string;
}

function tierFor(distance: number): Tier {
  if (distance <= 0.45) {
    return {
      label: "close match",
      fill: "var(--distance-good)",
      textClass: "text-[var(--distance-good-text)]",
    };
  }
  if (distance <= DISTANCE_THRESHOLD) {
    return {
      label: "borderline",
      fill: "var(--distance-borderline)",
      textClass: "text-[var(--distance-borderline-text)]",
    };
  }
  return {
    label: "past threshold",
    fill: "var(--distance-bad)",
    textClass: "text-[var(--distance-bad-text)]",
  };
}

export function DistanceBar({ distance }: { distance: number }) {
  const tier = tierFor(distance);
  const ratio =
    Math.min(Math.max(distance, 0), DISTANCE_SCALE_MAX) / DISTANCE_SCALE_MAX;
  const thresholdRatio = DISTANCE_THRESHOLD / DISTANCE_SCALE_MAX;

  return (
    <div className="flex items-center gap-3">
      <span className="shrink-0 text-[10px] tracking-wide text-muted uppercase">
        distance
      </span>
      <div
        className="relative h-1.5 w-full max-w-40 rounded-full"
        style={{ backgroundColor: "var(--bar-track)" }}
        role="img"
        aria-label={`Cosine distance ${distance.toFixed(4)} of a maximum ${DISTANCE_SCALE_MAX}. Refusal threshold is ${DISTANCE_THRESHOLD}.`}
      >
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{
            width: `${Math.max(ratio * 100, 2)}%`,
            backgroundColor: tier.fill,
          }}
        />
        <div
          className="absolute -top-1 -bottom-1 w-px"
          style={{
            left: `${thresholdRatio * 100}%`,
            backgroundColor: "var(--bar-threshold)",
          }}
          title={`Refusal threshold ${DISTANCE_THRESHOLD}`}
        />
      </div>
      <span className="font-mono text-xs tabular-nums text-foreground/70">
        {distance.toFixed(4)}
      </span>
      <span className={`text-xs ${tier.textClass}`}>{tier.label}</span>
    </div>
  );
}
