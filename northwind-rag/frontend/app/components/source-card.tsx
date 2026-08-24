import type { Source } from "../lib/types";
import { DistanceBar } from "./distance-bar";

/** Roughly the point where chunk text stops fitting in three lines. */
const CLAMP_CHAR_BUDGET = 180;

interface SourceCardProps {
  source: Source;
  expanded: boolean;
  onToggle: () => void;
}

export function SourceCard({ source, expanded, onToggle }: SourceCardProps) {
  const clampable = source.text.length > CLAMP_CHAR_BUDGET;
  const showFull = expanded || !clampable;

  return (
    <article
      id={`source-${source.index}`}
      className="rounded-lg border border-line bg-surface p-4 scroll-mt-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <div className="flex min-w-0 items-center gap-2">
          <span className="flex size-5 shrink-0 items-center justify-center rounded bg-accent-soft font-mono text-[11px] font-medium text-accent">
            {source.index}
          </span>
          <span className="truncate font-mono text-sm text-foreground">
            {source.source}
          </span>
          <span className="shrink-0 font-mono text-xs text-muted">
            chunk {source.chunk_index}
          </span>
        </div>

        {typeof source.rerank_score === "number" && (
          <span className="font-mono text-xs text-muted">
            rerank {source.rerank_score.toFixed(2)}
          </span>
        )}
      </div>

      <div className="mt-3">
        {showFull ? (
          <p className="text-sm leading-6 whitespace-pre-wrap text-foreground/80">
            {source.text}
          </p>
        ) : (
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={false}
            className="block w-full cursor-pointer text-left"
          >
            <span className="line-clamp-3 text-sm leading-6 text-foreground/80">
              {source.text}
            </span>
            <span className="mt-1 inline-block text-xs text-accent">
              Show full chunk
            </span>
          </button>
        )}

        {clampable && expanded && (
          <button
            type="button"
            onClick={onToggle}
            aria-expanded
            className="mt-1 cursor-pointer text-xs text-accent"
          >
            Collapse
          </button>
        )}
      </div>

      <div className="mt-4 border-t border-line pt-3">
        <DistanceBar distance={source.distance} />
      </div>
    </article>
  );
}
