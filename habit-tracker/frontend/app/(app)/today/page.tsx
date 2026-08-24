"use client";

import Link from "next/link";
import { useHabitStore } from "@/context/habit-store";
import { HabitCheckRow } from "@/components/habit-check-row";
import { EDIT_WINDOW_DAYS, formatDisplayDate, todayKey } from "@/lib/dates";
import {
  getEffectiveStatus,
  habitsForDate,
} from "@/lib/habits";
import { todayCompletion } from "@/lib/stats";

export default function TodayPage() {
  const { habits, entries, setStatus } = useHabitStore();
  const dateKey = todayKey();
  const scheduled = habitsForDate(habits, dateKey);
  const completion = todayCompletion(habits, entries);

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Today</h1>
          <p className="mt-1 text-sm text-muted">
            {formatDisplayDate(dateKey)}
            {completion.total > 0 && (
              <span>
                {" "}
                · {completion.done}/{completion.total} done
              </span>
            )}
          </p>
          <p className="mt-2 text-xs text-muted">
            Mark each habit done or not done by end of day. You can edit the last{" "}
            {EDIT_WINDOW_DAYS} days from the Dashboard.
          </p>
        </div>
        <Link
          href="/habits?new=1"
          className="shrink-0 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition hover:brightness-110"
        >
          Add new habit
        </Link>
      </div>

      {scheduled.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center">
          <p className="text-sm text-muted">
            No habits scheduled for today.
          </p>
          <Link
            href="/habits"
            className="mt-3 inline-block text-sm text-accent hover:underline"
          >
            Manage habits
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {scheduled.map((habit) => {
            const status = getEffectiveStatus(entries, habit.id, dateKey);
            const rowStatus =
              status === "done" || status === "not_done" ? status : "pending";
            return (
              <HabitCheckRow
                key={habit.id}
                name={habit.name}
                status={rowStatus}
                onDone={() => setStatus(habit.id, dateKey, "done")}
                onNotDone={() => setStatus(habit.id, dateKey, "not_done")}
                onClear={() => setStatus(habit.id, dateKey, null)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
