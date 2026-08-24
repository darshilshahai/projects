"use client";

import type { HabitStatus } from "@/lib/types";

type HabitCheckRowProps = {
  name: string;
  status: HabitStatus | "pending";
  onDone: () => void;
  onNotDone: () => void;
  onClear?: () => void;
};

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M4.5 10.5 8.2 14.2 15.5 5.8"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M5.5 5.5 14.5 14.5M14.5 5.5 5.5 14.5"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function HabitCheckRow({
  name,
  status,
  onDone,
  onNotDone,
  onClear,
}: HabitCheckRowProps) {
  return (
    <div className="animate-fade-up flex items-center gap-3 rounded-xl border border-border/70 bg-surface/60 px-4 py-3.5 transition hover:bg-surface">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{name}</p>
        <p className="mt-0.5 text-xs text-muted">
          {status === "done"
            ? "Done"
            : status === "not_done"
              ? "Not done"
              : "Not marked yet"}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={onDone}
          aria-label="Mark done"
          aria-pressed={status === "done"}
          className={`flex h-10 w-10 items-center justify-center rounded-lg transition ${
            status === "done"
              ? "bg-success/20 text-success ring-1 ring-success/40"
              : "bg-background text-success/50 hover:bg-success/10 hover:text-success"
          }`}
        >
          <CheckIcon className="h-5 w-5" />
        </button>
        <button
          type="button"
          onClick={onNotDone}
          aria-label="Mark not done"
          aria-pressed={status === "not_done"}
          className={`flex h-10 w-10 items-center justify-center rounded-lg transition ${
            status === "not_done"
              ? "bg-danger/20 text-danger ring-1 ring-danger/40"
              : "bg-background text-danger/50 hover:bg-danger/10 hover:text-danger"
          }`}
        >
          <XIcon className="h-5 w-5" />
        </button>
        {onClear && status !== "pending" && (
          <button
            type="button"
            onClick={onClear}
            className="rounded-lg px-2 py-2 text-xs text-muted transition hover:text-foreground"
            aria-label="Clear status"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
