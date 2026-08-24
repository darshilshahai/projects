"use client";

import Link from "next/link";
import { useHabitStore } from "@/context/habit-store";
import { ContributionSection } from "@/components/contribution-grid";
import { MonthlyMatrix } from "@/components/monthly-matrix";
import { StatsSummary } from "@/components/stats-summary";
import { activeHabits } from "@/lib/habits";
import { overallStreak, todayCompletion } from "@/lib/stats";

export default function DashboardPage() {
  const { habits, entries, cycleStatus } = useHabitStore();
  const active = activeHabits(habits);
  const now = new Date();
  const completion = todayCompletion(habits, entries, now);
  const streak = overallStreak(habits, entries, now);

  return (
    <div className="animate-fade-up space-y-10">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted">
          Your progress at a glance. Cells from today and the past 7 days are
          editable.
        </p>
      </div>

      {active.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center">
          <p className="text-sm text-muted">
            Add habits to see your progress matrix and consistency grids.
          </p>
          <Link
            href="/habits"
            className="mt-3 inline-block text-sm text-accent hover:underline"
          >
            Go to Habits
          </Link>
        </div>
      ) : (
        <>
          <StatsSummary
            activeHabits={active.length}
            todayPercent={completion.percent}
            todayDone={completion.done}
            todayTotal={completion.total}
            streak={streak}
          />

          <MonthlyMatrix
            habits={active}
            entries={entries}
            year={now.getFullYear()}
            monthIndex={now.getMonth()}
            onCycle={cycleStatus}
          />

          <ContributionSection
            habits={active}
            entries={entries}
            onCycle={cycleStatus}
          />
        </>
      )}
    </div>
  );
}
