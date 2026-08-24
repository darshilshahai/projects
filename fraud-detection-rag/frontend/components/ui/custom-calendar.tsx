"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useFloatingPosition } from "@/lib/use-floating-position";
import { cn, formatDate } from "@/lib/utils";

interface CustomCalendarProps {
  label?: string;
  value: Date | null;
  onChange: (date: Date | null) => void;
  placeholder?: string;
  className?: string;
}

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const PANEL_WIDTH = 288;

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function buildMonthGrid(year: number, month: number) {
  const firstDay = new Date(year, month, 1);
  const startOffset = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: Array<Date | null> = [];

  for (let i = 0; i < startOffset; i += 1) {
    cells.push(null);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push(new Date(year, month, day));
  }

  while (cells.length % 7 !== 0) {
    cells.push(null);
  }

  return cells;
}

export function CustomCalendar({
  label,
  value,
  onChange,
  placeholder = "Select date",
  className,
}: CustomCalendarProps) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const today = new Date();
  const [viewDate, setViewDate] = useState(value ?? today);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const floatingStyle = useFloatingPosition(open, triggerRef);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;

      if (
        triggerRef.current?.contains(target) ||
        panelRef.current?.contains(target)
      ) {
        return;
      }

      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const monthLabel = viewDate.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  const cells = buildMonthGrid(viewDate.getFullYear(), viewDate.getMonth());

  const panelStyle = {
    ...floatingStyle,
    width: PANEL_WIDTH,
    maxWidth: "calc(100vw - 1rem)",
  };

  const panel =
    open && mounted ? (
      <div
        ref={panelRef}
        style={panelStyle}
        className="animate-scale-in rounded-2xl border border-border bg-card-elevated p-4 shadow-[var(--shadow-lg)]"
      >
        <div className="mb-4 flex items-center justify-between">
          <button
            type="button"
            aria-label="Previous month"
            onClick={() =>
              setViewDate(
                new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1),
              )
            }
            className="rounded-lg p-2 text-muted transition-colors hover:bg-muted-bg hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <p className="text-sm font-semibold text-foreground">{monthLabel}</p>
          <button
            type="button"
            aria-label="Next month"
            onClick={() =>
              setViewDate(
                new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1),
              )
            }
            className="rounded-lg p-2 text-muted transition-colors hover:bg-muted-bg hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        <div className="mb-2 grid grid-cols-7 gap-1">
          {WEEKDAYS.map((day) => (
            <div
              key={day}
              className="py-1 text-center text-[11px] font-medium uppercase tracking-wide text-muted"
            >
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {cells.map((date, index) => {
            if (!date) {
              return <div key={`empty-${index}`} className="h-9" />;
            }

            const isSelected = value ? sameDay(date, value) : false;
            const isToday = sameDay(date, today);

            return (
              <button
                key={date.toISOString()}
                type="button"
                onClick={() => {
                  onChange(date);
                  setOpen(false);
                }}
                className={cn(
                  "flex h-9 items-center justify-center rounded-xl text-sm transition-colors",
                  isSelected
                    ? "bg-primary text-white shadow-sm"
                    : "text-foreground hover:bg-primary-soft",
                  isToday && !isSelected && "ring-1 ring-primary/30",
                )}
              >
                {date.getDate()}
              </button>
            );
          })}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
          <button
            type="button"
            onClick={() => {
              onChange(today);
              setViewDate(today);
              setOpen(false);
            }}
            className="text-sm font-medium text-primary hover:text-primary-hover"
          >
            Today
          </button>
          <button
            type="button"
            onClick={() => {
              onChange(null);
              setOpen(false);
            }}
            className="text-sm text-muted hover:text-foreground"
          >
            Clear
          </button>
        </div>
      </div>
    ) : null;

  return (
    <div className={cn(className)}>
      {label ? (
        <label className="mb-2 block text-sm font-medium text-foreground">
          {label}
        </label>
      ) : null}

      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((current) => !current)}
        className={cn(
          "flex h-11 w-full items-center justify-between rounded-xl border border-border bg-card px-4 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]",
          open && "border-primary shadow-sm",
        )}
      >
        <span className={cn(!value && "text-muted")}>
          {value ? formatDate(value) : placeholder}
        </span>
        <span className="rounded-lg bg-primary-soft px-2 py-1 text-xs font-medium text-primary">
          Calendar
        </span>
      </button>

      {mounted && panel ? createPortal(panel, document.body) : null}
    </div>
  );
}
