"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { API_BASE_URL, ApiError, ask, checkHealth } from "../lib/api";
import { DISTANCE_THRESHOLD, EXAMPLE_QUESTIONS } from "../lib/constants";
import type { AskResponse, RefusalGate } from "../lib/types";
import { SourceCard } from "./source-card";

type HealthState =
  | { status: "checking" }
  | { status: "ok"; chunks: number }
  | { status: "down" };

async function fetchHealth(): Promise<HealthState> {
  try {
    const { chunks } = await checkHealth();
    return { status: "ok", chunks };
  } catch {
    return { status: "down" };
  }
}

const REFUSAL_COPY: Record<RefusalGate, { gate: string; detail: string }> = {
  distance_threshold: {
    gate: "Distance threshold",
    detail:
      "No retrieved chunk was close enough to the question, so the model was never called.",
  },
  llm_grounding: {
    gate: "LLM grounding rule",
    detail:
      "Chunks were retrieved, but the model could not support an answer with them.",
  },
};

interface AskPanelProps {
  healthRefreshKey?: number;
}

export function AskPanel({ healthRefreshKey = 0 }: AskPanelProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [emptyWarning, setEmptyWarning] = useState(false);
  const [expanded, setExpanded] = useState<number[]>([]);
  const [health, setHealth] = useState<HealthState>({ status: "checking" });

  const inputRef = useRef<HTMLInputElement>(null);
  const requestId = useRef(0);
  const wasDown = useRef(false);

  const applyHealth = useCallback((next: HealthState) => {
    wasDown.current = next.status === "down";
    setHealth(next);
  }, []);

  const refreshHealth = useCallback(async () => {
    setHealth({ status: "checking" });
    applyHealth(await fetchHealth());
  }, [applyHealth]);

  useEffect(() => {
    let cancelled = false;
    void fetchHealth().then((next) => {
      if (!cancelled) applyHealth(next);
    });
    return () => {
      cancelled = true;
    };
  }, [applyHealth, healthRefreshKey]);

  const runQuery = useCallback(
    async (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed) {
        setEmptyWarning(true);
        inputRef.current?.focus();
        return;
      }

      const id = ++requestId.current;
      setEmptyWarning(false);
      setError(null);
      setResult(null);
      setExpanded([]);
      setLoading(true);

      try {
        const response = await ask(trimmed);
        if (id !== requestId.current) return;
        setResult(response);
        if (wasDown.current) void refreshHealth();
      } catch (caught) {
        if (id !== requestId.current) return;
        if (caught instanceof ApiError && caught.unreachable) {
          wasDown.current = true;
          setHealth({ status: "down" });
        } else {
          setError(
            caught instanceof ApiError
              ? caught.message
              : "Something went wrong while asking the backend.",
          );
        }
      } finally {
        if (id === requestId.current) setLoading(false);
      }
    },
    [refreshHealth],
  );

  const toggleSource = useCallback((index: number) => {
    setExpanded((current) =>
      current.includes(index)
        ? current.filter((i) => i !== index)
        : [...current, index],
    );
  }, []);

  const jumpToSource = useCallback((index: number) => {
    setExpanded((current) =>
      current.includes(index) ? current : [...current, index],
    );
    document
      .getElementById(`source-${index}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  const backendDown = health.status === "down";

  return (
    <div className="flex flex-col gap-8">
      {backendDown && (
        <div className="rounded-lg border border-warning-border bg-warning-bg p-4">
          <p className="text-sm font-medium text-warning-text">
            Backend unreachable
          </p>
          <p className="mt-1 text-sm text-warning-text/85">
            Nothing is responding at{" "}
            <span className="font-mono">{API_BASE_URL}</span>. Start the FastAPI
            server, then try again.
          </p>
          <button
            type="button"
            onClick={() => void refreshHealth()}
            className="mt-3 cursor-pointer rounded-md border border-warning-border bg-surface px-3 py-1.5 text-sm text-warning-text hover:opacity-80"
          >
            Retry connection
          </button>
        </div>
      )}

      <section>
        <p className="text-xs tracking-wide text-muted uppercase">Try one</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((example) => (
            <button
              key={example.question}
              type="button"
              disabled={loading}
              onClick={() => {
                setQuestion(example.question);
                void runQuery(example.question);
              }}
              className="cursor-pointer rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-foreground/80 hover:border-accent/40 hover:text-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {example.question}
              {example.refuses && (
                <span className="ml-2 text-xs text-muted">gets refused</span>
              )}
            </button>
          ))}
        </div>
      </section>

      <div className="flex flex-col gap-2">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void runQuery(question);
          }}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <input
            ref={inputRef}
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
              if (emptyWarning) setEmptyWarning(false);
            }}
            placeholder="Ask about the policy documents…"
            aria-label="Question"
            aria-invalid={emptyWarning}
            autoComplete="off"
            className="w-full rounded-lg border border-line bg-surface px-4 py-3 text-base outline-none placeholder:text-muted/70 focus:border-accent focus:ring-2 focus:ring-accent/15"
          />
          <button
            type="submit"
            disabled={loading}
            className="flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-base font-medium text-white hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading && (
              <span
                aria-hidden
                className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
              />
            )}
            {loading ? "Asking" : "Ask"}
          </button>
        </form>

        {emptyWarning && (
          <p className="text-sm text-muted">Type a question first.</p>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-warning-border bg-warning-bg p-4">
          <p className="text-sm font-medium text-warning-text">Request failed</p>
          <p className="mt-1 text-sm text-warning-text/85">{error}</p>
        </div>
      )}

      <div aria-live="polite" aria-busy={loading}>
        {loading && (
          <div className="animate-pulse rounded-lg border border-line bg-surface p-6">
            <p className="text-sm text-muted">
              Retrieving chunks and grounding an answer…
            </p>
          </div>
        )}

        {!loading && result && (
          <Result
            result={result}
            expanded={expanded}
            onToggleSource={toggleSource}
            onCitationClick={jumpToSource}
          />
        )}
      </div>

      {!loading && !result && !error && !backendDown && (
        <p className="text-sm text-muted">
          {health.status === "ok"
            ? `Index ready — ${health.chunks} chunks. Ask a question to see the retrieved evidence behind the answer.`
            : "Checking the backend…"}
        </p>
      )}
    </div>
  );
}

interface ResultProps {
  result: AskResponse;
  expanded: number[];
  onToggleSource: (index: number) => void;
  onCitationClick: (index: number) => void;
}

function Result({
  result,
  expanded,
  onToggleSource,
  onCitationClick,
}: ResultProps) {
  const refusal = result.refused_by ? REFUSAL_COPY[result.refused_by] : null;

  return (
    <div className="flex flex-col gap-8">
      <section
        className={
          result.refused
            ? "rounded-lg border border-refusal-border bg-refusal-bg p-6"
            : "rounded-lg border border-line bg-surface p-6"
        }
      >
        {result.refused && (
          <p className="mb-3 flex flex-wrap items-center gap-2 text-xs tracking-wide text-refusal-text uppercase">
            Refused
            {refusal && (
              <span className="rounded border border-refusal-border bg-refusal-badge-bg px-1.5 py-0.5 font-mono text-[11px] normal-case">
                {result.refused_by}
              </span>
            )}
          </p>
        )}

        <p
          className={`text-lg leading-8 whitespace-pre-wrap ${
            result.refused ? "text-refusal-text" : "text-foreground"
          }`}
        >
          <AnswerText answer={result.answer} onCitationClick={onCitationClick} />
        </p>

        {refusal && (
          <p className="mt-4 border-t border-refusal-border pt-3 text-sm text-refusal-text/80">
            <span className="font-medium">{refusal.gate}</span> — {refusal.detail}
          </p>
        )}

        {result.refused && result.gate_distance != null && (
          <p className="mt-3 font-mono text-xs leading-5 text-refusal-text/80">
            Gate 1 closest match: {result.gate_distance.toFixed(4)}
            {result.refused_by === "llm_grounding" && (
              <>
                {" "}
                — under threshold {DISTANCE_THRESHOLD}, passed to LLM. Sources
                below are post-rerank; the closest pre-rerank chunk is not
                shown.
              </>
            )}
            {result.refused_by === "distance_threshold" && (
              <> — above threshold {DISTANCE_THRESHOLD}, LLM not called.</>
            )}
          </p>
        )}
      </section>

      <section>
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h2 className="text-sm font-medium">
            Sources
            <span className="ml-2 font-normal text-muted">
              {result.sources.length} retrieved
            </span>
          </h2>
          <p className="text-xs text-muted">
            Chunks sent to the LLM (post-rerank). Shorter cosine distance is a
            closer match. The tick marks the refusal threshold.
          </p>
        </div>

        {result.sources.length === 0 ? (
          <p className="mt-3 rounded-lg border border-dashed border-line p-4 text-sm text-muted">
            No chunks were returned for this question.
          </p>
        ) : (
          <div className="mt-3 flex flex-col gap-3">
            {result.sources.map((source) => (
              <SourceCard
                key={`${source.source}-${source.chunk_index}-${source.index}`}
                source={source}
                expanded={expanded.includes(source.index)}
                onToggle={() => onToggleSource(source.index)}
              />
            ))}
          </div>
        )}
      </section>

      <footer className="flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-line pt-3 font-mono text-xs text-muted">
        <span>{result.latency_ms.toLocaleString()} ms</span>
        <span>
          {result.usage
            ? `${result.usage.prompt_tokens.toLocaleString()} prompt + ${result.usage.completion_tokens.toLocaleString()} completion tokens`
            : "no tokens spent"}
        </span>
        <span>{result.sources.length} chunks</span>
      </footer>
    </div>
  );
}

function AnswerText({
  answer,
  onCitationClick,
}: {
  answer: string;
  onCitationClick: (index: number) => void;
}) {
  const parts = answer.split(/(\[\d+\])/g);

  return (
    <>
      {parts.map((part, i) => {
        const match = /^\[(\d+)\]$/.exec(part);
        if (!match) return <span key={i}>{part}</span>;

        const index = Number(match[1]);
        return (
          <button
            key={i}
            type="button"
            onClick={() => onCitationClick(index)}
            title={`Jump to source ${index}`}
            className="mx-0.5 cursor-pointer rounded bg-accent-soft px-1.5 align-[0.1em] font-mono text-xs text-accent hover:bg-accent hover:text-white"
          >
            {index}
          </button>
        );
      })}
    </>
  );
}
