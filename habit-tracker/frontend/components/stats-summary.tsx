"use client";

type StatsSummaryProps = {
  activeHabits: number;
  todayPercent: number;
  todayDone: number;
  todayTotal: number;
  streak: number;
};

export function StatsSummary({
  activeHabits,
  todayPercent,
  todayDone,
  todayTotal,
  streak,
}: StatsSummaryProps) {
  const items = [
    {
      label: "Active habits",
      value: String(activeHabits),
    },
    {
      label: "Today",
      value: todayTotal === 0 ? "—" : `${todayPercent}%`,
      hint: todayTotal > 0 ? `${todayDone}/${todayTotal}` : undefined,
    },
    {
      label: "Day streak",
      value: String(streak),
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-xl border border-border/70 bg-surface/50 px-3 py-3 sm:px-4"
        >
          <p className="text-[11px] uppercase tracking-wide text-muted">
            {item.label}
          </p>
          <p className="mt-1 font-mono text-xl font-medium tracking-tight sm:text-2xl">
            {item.value}
          </p>
          {item.hint && (
            <p className="mt-0.5 text-xs text-muted">{item.hint}</p>
          )}
        </div>
      ))}
    </div>
  );
}
