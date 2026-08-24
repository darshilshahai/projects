"use client";

import type { Habit, HabitEntry } from "@/lib/types";
import {
  dateRangeKeys,
  isEditableDate,
  todayKey,
} from "@/lib/dates";
import {
  getEffectiveStatus,
  isHabitScheduledOn,
} from "@/lib/habits";
import { habitCompletionRate, habitStreak } from "@/lib/stats";

const GRID_DAYS = 112; // 16 weeks

type ContributionGridProps = {
  habit: Habit;
  entries: HabitEntry[];
  onCycle: (habitId: string, dateKey: string) => void;
};

export function ContributionGrid({
  habit,
  entries,
  onCycle,
}: ContributionGridProps) {
  const today = todayKey();
  const keys = dateRangeKeys(today, GRID_DAYS);
  const streak = habitStreak(habit, entries);
  const rate = habitCompletionRate(habit, entries, 30);

  // Column-major weeks (GitHub style): 7 rows (Sun–Sat), ~16 columns
  const weeks: string[][] = [];
  let week: string[] = [];
  const firstWeekday = new Date(
    Number(keys[0].slice(0, 4)),
    Number(keys[0].slice(5, 7)) - 1,
    Number(keys[0].slice(8, 10)),
  ).getDay();

  for (let i = 0; i < firstWeekday; i++) {
    week.push("");
  }
  for (const key of keys) {
    week.push(key);
    if (week.length === 7) {
      weeks.push(week);
      week = [];
    }
  }
  if (week.length) {
    while (week.length < 7) week.push("");
    weeks.push(week);
  }

  return (
    <div className="animate-fade-up rounded-xl border border-border/70 bg-surface/40 p-4">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-medium">{habit.name}</h3>
        <p className="font-mono text-xs text-muted">
          {streak}d streak · {rate}% / 30d
        </p>
      </div>
      <div className="overflow-x-auto">
        <div className="inline-flex gap-[3px]">
          {weeks.map((w, wi) => (
            <div key={wi} className="flex flex-col gap-[3px]">
              {w.map((key, di) => {
                if (!key) {
                  return (
                    <div
                      key={`empty-${wi}-${di}`}
                      className="h-[11px] w-[11px]"
                    />
                  );
                }
                const scheduled = isHabitScheduledOn(habit, key);
                const editable = scheduled && isEditableDate(key);
                const status = scheduled
                  ? getEffectiveStatus(entries, habit.id, key)
                  : "unscheduled";

                let bg = "bg-cell-empty";
                if (!scheduled) bg = "bg-transparent";
                else if (status === "done") bg = "bg-cell-done";
                else if (status === "not_done") bg = "bg-cell-miss";
                else if (status === "pending") bg = "bg-cell-pending";

                return (
                  <button
                    key={key}
                    type="button"
                    disabled={!editable}
                    onClick={() => onCycle(habit.id, key)}
                    title={`${key}${scheduled ? "" : " (off)"}`}
                    className={`h-[11px] w-[11px] rounded-[2px] ${bg} ${
                      editable
                        ? "cursor-pointer hover:ring-1 hover:ring-accent/70"
                        : "cursor-default"
                    } ${key === today && scheduled ? "ring-1 ring-white/30" : ""}`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

type ContributionSectionProps = {
  habits: Habit[];
  entries: HabitEntry[];
  onCycle: (habitId: string, dateKey: string) => void;
};

export function ContributionSection({
  habits,
  entries,
  onCycle,
}: ContributionSectionProps) {
  return (
    <section>
      <div className="mb-3">
        <h2 className="text-sm font-medium">Consistency</h2>
        <p className="mt-0.5 text-xs text-muted">
          Last ~16 weeks per habit · editable cells within the last 7 days
        </p>
      </div>
      <div className="flex flex-col gap-3">
        {habits.map((habit) => (
          <ContributionGrid
            key={habit.id}
            habit={habit}
            entries={entries}
            onCycle={onCycle}
          />
        ))}
      </div>
    </section>
  );
}
