"use client";

import type { Habit, HabitEntry } from "@/lib/types";
import { DAY_LABELS } from "@/lib/types";
import {
  formatMonthYear,
  isEditableDate,
  isFutureDate,
  monthMeta,
  todayKey,
} from "@/lib/dates";
import {
  getEffectiveStatus,
  isHabitScheduledOn,
} from "@/lib/habits";

type MonthlyMatrixProps = {
  habits: Habit[];
  entries: HabitEntry[];
  year: number;
  monthIndex: number;
  onCycle: (habitId: string, dateKey: string) => void;
};

function cellClass(
  status: string,
  unscheduled: boolean,
  future: boolean,
) {
  if (unscheduled || future) {
    return "bg-transparent border border-transparent";
  }
  if (status === "done") return "bg-cell-done";
  if (status === "not_done") return "bg-cell-miss";
  if (status === "pending") return "bg-cell-pending";
  return "bg-cell-empty";
}

export function MonthlyMatrix({
  habits,
  entries,
  year,
  monthIndex,
  onCycle,
}: MonthlyMatrixProps) {
  const { days } = monthMeta(year, monthIndex);
  const today = todayKey();

  return (
    <section>
      <div className="mb-3 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium">This month</h2>
          <p className="mt-0.5 text-xs text-muted">
            {formatMonthYear(year, monthIndex)} · tap a cell to cycle status
            (last 7 days + today)
          </p>
        </div>
      </div>
      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-full">
          <div
            className="grid gap-px"
            style={{
              gridTemplateColumns: `minmax(7rem, 9rem) repeat(${days.length}, minmax(1.35rem, 1.5rem))`,
            }}
          >
            <div />
            {days.map((d) => (
              <div
                key={`n-${d.day}`}
                className={`pb-1 text-center font-mono text-[10px] ${
                  d.dateKey === today ? "text-accent" : "text-muted"
                }`}
              >
                {d.day}
              </div>
            ))}
            <div />
            {days.map((d) => (
              <div
                key={`w-${d.day}`}
                className={`pb-2 text-center font-mono text-[9px] ${
                  d.weekday === 0 || d.weekday === 6
                    ? "text-muted/60"
                    : "text-muted"
                }`}
              >
                {DAY_LABELS[d.weekday]}
              </div>
            ))}

            {habits.map((habit) => (
              <div key={habit.id} className="contents">
                <div className="flex items-center truncate pr-3 text-xs text-foreground/90">
                  {habit.name}
                </div>
                {days.map((d) => {
                  const scheduled = isHabitScheduledOn(habit, d.dateKey);
                  const future = isFutureDate(d.dateKey);
                  const editable =
                    scheduled && !future && isEditableDate(d.dateKey);
                  const status = scheduled
                    ? getEffectiveStatus(entries, habit.id, d.dateKey)
                    : "unscheduled";
                  const weekStart = d.weekday === 1;

                  return (
                    <button
                      key={`${habit.id}-${d.dateKey}`}
                      type="button"
                      disabled={!editable}
                      onClick={() => onCycle(habit.id, d.dateKey)}
                      title={
                        !scheduled
                          ? "Not scheduled"
                          : future
                            ? "Future day"
                            : editable
                              ? `${habit.name} · ${d.dateKey}`
                              : "Outside edit window"
                      }
                      className={`relative h-5 w-full rounded-[3px] transition ${cellClass(
                        status,
                        !scheduled,
                        future,
                      )} ${editable ? "cursor-pointer hover:ring-1 hover:ring-accent/60" : "cursor-default"} ${
                        weekStart ? "ml-0.5" : ""
                      } ${d.dateKey === today && scheduled ? "ring-1 ring-accent/40" : ""}`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-cell-done" />{" "}
          Done
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-cell-miss" />{" "}
          Not done
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-cell-pending" />{" "}
          Pending
        </span>
      </div>
    </section>
  );
}
