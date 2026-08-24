"use client";

import { FormEvent, useState } from "react";
import { useHabitStore } from "@/context/habit-store";
import { ApiError } from "@/lib/api/client";
import { MAX_MANIFESTATIONS } from "@/lib/types";

export default function ManifestationsPage() {
  const {
    manifestations,
    addManifestation,
    editManifestation,
    removeManifestation,
  } = useHabitStore();
  const [text, setText] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const atLimit = manifestations.length >= MAX_MANIFESTATIONS;

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || atLimit) return;
    setBusy(true);
    setError("");
    try {
      await addManifestation(text);
      setText("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Failed to add line",
      );
    } finally {
      setBusy(false);
    }
  }

  function startEdit(id: string, current: string) {
    setEditingId(id);
    setEditText(current);
    setError("");
  }

  async function saveEdit(e: FormEvent) {
    e.preventDefault();
    if (!editingId || !editText.trim()) return;
    setBusy(true);
    setError("");
    try {
      await editManifestation(editingId, editText);
      setEditingId(null);
      setEditText("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Failed to save",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="animate-fade-up space-y-8">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Manifestations</h1>
        <p className="mt-1 text-sm text-muted">
          Write lines that keep you focused. They appear on every screen under
          Today&apos;s focus. You can save up to {MAX_MANIFESTATIONS} lines (
          {manifestations.length}/{MAX_MANIFESTATIONS}).
        </p>
      </div>

      <form
        onSubmit={onAdd}
        className="flex flex-col gap-3 rounded-xl border border-border bg-surface/50 p-4 sm:flex-row sm:items-end"
      >
        <label className="flex min-w-0 flex-1 flex-col gap-1.5">
          <span className="text-xs text-muted">New line</span>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. I show up for myself every day."
            maxLength={160}
            disabled={atLimit || busy}
            className="rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition focus:border-accent disabled:opacity-50"
          />
        </label>
        <button
          type="submit"
          disabled={atLimit || busy || !text.trim()}
          className="rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-50"
        >
          Add
        </button>
      </form>

      {atLimit && (
        <p className="text-xs text-muted">
          Limit reached. Delete a line to add a new one.
        </p>
      )}
      {error && <p className="text-sm text-danger">{error}</p>}

      {manifestations.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center">
          <p className="text-sm text-muted">
            No personal lines yet. AI suggestions show in Today&apos;s focus
            until you add your own.
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {manifestations.map((item) => (
            <li
              key={item.id}
              className="rounded-xl border border-border/70 bg-surface/40 px-4 py-3"
            >
              {editingId === item.id ? (
                <form
                  onSubmit={saveEdit}
                  className="flex flex-col gap-3 sm:flex-row sm:items-center"
                >
                  <input
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    maxLength={160}
                    autoFocus
                    disabled={busy}
                    className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent"
                  />
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={busy}
                      className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="rounded-md px-3 py-1.5 text-xs text-muted hover:text-foreground"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm leading-relaxed">{item.text}</p>
                  <div className="flex shrink-0 gap-2">
                    <button
                      type="button"
                      onClick={() => startEdit(item.id, item.text)}
                      className="rounded-md px-2.5 py-1.5 text-xs text-muted transition hover:bg-surface-hover hover:text-foreground"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void (async () => {
                          setError("");
                          try {
                            await removeManifestation(item.id);
                          } catch (err) {
                            setError(
                              err instanceof Error
                                ? err.message
                                : "Failed to delete",
                            );
                          }
                        })();
                      }}
                      className="rounded-md px-2.5 py-1.5 text-xs text-muted transition hover:text-danger"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
