"use client";

import { FormEvent, useState } from "react";
import type { Habit } from "@/lib/types";
import { ALL_DAYS, DAY_NAMES } from "@/lib/types";

type HabitFormProps = {
  initial?: Habit;
  onSubmit: (name: string, daysOfWeek: number[]) => void;
  onCancel?: () => void;
  submitLabel?: string;
};

export function HabitForm({
  initial,
  onSubmit,
  onCancel,
  submitLabel = "Add habit",
}: HabitFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [days, setDays] = useState<number[]>(
    initial?.daysOfWeek ?? [...ALL_DAYS],
  );

  function toggleDay(day: number) {
    setDays((prev) => {
      if (prev.includes(day)) {
        const next = prev.filter((d) => d !== day);
        return next.length === 0 ? prev : next;
      }
      return [...prev, day].sort((a, b) => a - b);
    });
  }

  function selectEveryDay() {
    setDays([...ALL_DAYS]);
  }

  function onFormSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit(name.trim(), days);
    if (!initial) {
      setName("");
      setDays([...ALL_DAYS]);
    }
  }

  return (
    <form onSubmit={onFormSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-muted">Name</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Read Book"
          className="rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none transition focus:border-accent"
          autoFocus={!initial}
        />
      </label>
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs text-muted">Schedule</span>
          <button
            type="button"
            onClick={selectEveryDay}
            className="text-xs text-muted transition hover:text-foreground"
          >
            Every day
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {DAY_NAMES.map((label, index) => {
            const active = days.includes(index);
            return (
              <button
                key={label + index}
                type="button"
                onClick={() => toggleDay(index)}
                className={`h-9 min-w-10 rounded-md px-2 text-xs font-medium transition ${
                  active
                    ? "bg-accent text-white"
                    : "bg-surface text-muted hover:text-foreground"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:brightness-110"
        >
          {submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-4 py-2 text-sm text-muted transition hover:text-foreground"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
