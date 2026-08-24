"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useHabitStore } from "@/context/habit-store";
import { HabitForm } from "@/components/habit-form";
import { activeHabits } from "@/lib/habits";
import { DAY_NAMES } from "@/lib/types";
import type { Habit } from "@/lib/types";

function scheduleLabel(daysOfWeek: number[]) {
  if (daysOfWeek.length === 7) return "Every day";
  return daysOfWeek.map((d) => DAY_NAMES[d]).join(", ");
}

function HabitsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { habits, addHabit, editHabit, removeHabit } = useHabitStore();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [manualCreate, setManualCreate] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [error, setError] = useState("");

  const fromUrl = searchParams.get("new") === "1";
  const showCreate = (fromUrl || manualCreate) && !editingId;

  function openCreate() {
    setEditingId(null);
    setManualCreate(true);
  }

  function closeCreate() {
    setManualCreate(false);
    if (fromUrl) router.replace("/habits");
  }

  const list = activeHabits(habits);
  const archived = habits.filter((h) => h.archived);
  const editing = habits.find((h) => h.id === editingId) as Habit | undefined;

  return (
    <div className="animate-fade-up space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Habits</h1>
          <p className="mt-1 text-sm text-muted">
            Create and schedule what you want to track.
          </p>
        </div>
        {!showCreate && !editingId && (
          <button
            type="button"
            onClick={openCreate}
            className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition hover:brightness-110"
          >
            Add habit
          </button>
        )}
      </div>

      {(showCreate || editing) && (
        <div className="rounded-xl border border-border bg-surface/50 p-4">
          <h2 className="mb-4 text-sm font-medium">
            {editing ? "Edit habit" : "New habit"}
          </h2>
          {error && <p className="mb-3 text-sm text-danger">{error}</p>}
          <HabitForm
            key={editing?.id ?? "new"}
            initial={editing}
            submitLabel={editing ? "Save" : "Add habit"}
            onCancel={() => {
              closeCreate();
              setEditingId(null);
              setError("");
            }}
            onSubmit={(name, daysOfWeek) => {
              void (async () => {
                setError("");
                try {
                  if (editing) {
                    await editHabit(editing.id, { name, daysOfWeek });
                    setEditingId(null);
                  } else {
                    await addHabit(name, daysOfWeek);
                    closeCreate();
                  }
                } catch (err) {
                  setError(
                    err instanceof Error ? err.message : "Failed to save habit",
                  );
                }
              })();
            }}
          />
        </div>
      )}

      {list.length === 0 && !showCreate ? (
        <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center">
          <p className="text-sm text-muted">No habits yet.</p>
          <button
            type="button"
            onClick={openCreate}
            className="mt-3 text-sm text-accent hover:underline"
          >
            Create your first habit
          </button>
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {list.map((habit) => (
            <li
              key={habit.id}
              className="flex flex-col gap-3 rounded-xl border border-border/70 bg-surface/40 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{habit.name}</p>
                <p className="mt-0.5 text-xs text-muted">
                  {scheduleLabel(habit.daysOfWeek)}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    closeCreate();
                    setEditingId(habit.id);
                  }}
                  className="rounded-md px-2.5 py-1.5 text-xs text-muted transition hover:bg-surface-hover hover:text-foreground"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => {
                    void editHabit(habit.id, { archived: true });
                  }}
                  className="rounded-md px-2.5 py-1.5 text-xs text-muted transition hover:bg-surface-hover hover:text-foreground"
                >
                  Archive
                </button>
                {confirmDelete === habit.id ? (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        void removeHabit(habit.id);
                        setConfirmDelete(null);
                      }}
                      className="rounded-md px-2.5 py-1.5 text-xs text-danger transition hover:bg-surface-hover"
                    >
                      Confirm delete
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfirmDelete(null)}
                      className="rounded-md px-2.5 py-1.5 text-xs text-muted"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(habit.id)}
                    className="rounded-md px-2.5 py-1.5 text-xs text-muted transition hover:text-danger"
                  >
                    Delete
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {archived.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-medium text-muted">Archived</h2>
          <ul className="flex flex-col gap-2">
            {archived.map((habit) => (
              <li
                key={habit.id}
                className="flex items-center justify-between rounded-xl border border-border/40 px-4 py-3 opacity-70"
              >
                <p className="text-sm">{habit.name}</p>
                <button
                  type="button"
                  onClick={() => {
                    void editHabit(habit.id, { archived: false });
                  }}
                  className="text-xs text-muted hover:text-foreground"
                >
                  Restore
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-xs text-muted">
        Tip: check in on{" "}
        <Link href="/today" className="text-foreground underline-offset-2 hover:underline">
          Today
        </Link>{" "}
        and review progress on{" "}
        <Link href="/dashboard" className="text-foreground underline-offset-2 hover:underline">
          Dashboard
        </Link>
        .
      </p>
    </div>
  );
}

export default function HabitsPage() {
  return (
    <Suspense
      fallback={
        <div className="text-sm text-muted">Loading habits…</div>
      }
    >
      <HabitsPageContent />
    </Suspense>
  );
}
