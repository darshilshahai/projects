"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import * as authApi from "@/lib/api/auth";
import * as entriesApi from "@/lib/api/entries";
import * as habitsApi from "@/lib/api/habits";
import * as inspirationApi from "@/lib/api/inspiration";
import * as manifestationsApi from "@/lib/api/manifestations";
import { ApiError } from "@/lib/api/client";
import {
  authToSession,
  clearStoredAuth,
  getStoredAuth,
  setStoredAuth,
  type StoredAuth,
} from "@/lib/auth-token";
import { addDays, toDateKey, todayKey } from "@/lib/dates";
import { cycleEntryStatus, getEntry } from "@/lib/habits";
import type {
  Habit,
  HabitEntry,
  HabitStatus,
  Inspiration,
  Manifestation,
  Session,
} from "@/lib/types";

type HabitStoreValue = {
  ready: boolean;
  dataLoading: boolean;
  session: Session | null;
  habits: Habit[];
  entries: HabitEntry[];
  manifestations: Manifestation[];
  inspiration: Inspiration | null;
  error: string | null;
  clearError: () => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  addHabit: (name: string, daysOfWeek?: number[]) => Promise<void>;
  editHabit: (
    id: string,
    patch: Partial<Pick<Habit, "name" | "daysOfWeek" | "archived">>,
  ) => Promise<void>;
  removeHabit: (id: string) => Promise<void>;
  cycleStatus: (habitId: string, dateKey: string) => Promise<void>;
  setStatus: (
    habitId: string,
    dateKey: string,
    status: HabitStatus | null,
  ) => Promise<void>;
  addManifestation: (text: string) => Promise<void>;
  editManifestation: (id: string, text: string) => Promise<void>;
  removeManifestation: (id: string) => Promise<void>;
  refreshInspiration: () => Promise<void>;
};

const HabitStoreContext = createContext<HabitStoreValue | null>(null);

function sessionFromAuthResponse(
  res: Awaited<ReturnType<typeof authApi.signIn>>,
): StoredAuth {
  return {
    accessToken: res.accessToken,
    refreshToken: res.refreshToken,
    email: (res.user.email || "").toLowerCase(),
    userId: res.user.id,
    signedInAt: new Date().toISOString(),
  };
}

function entryRange() {
  const to = todayKey();
  const from = toDateKey(addDays(new Date(), -120));
  return { from, to };
}

export function HabitStoreProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [habits, setHabits] = useState<Habit[]>([]);
  const [entries, setEntries] = useState<HabitEntry[]>([]);
  const [manifestations, setManifestations] = useState<Manifestation[]>([]);
  const [inspiration, setInspiration] = useState<Inspiration | null>(null);
  const [error, setError] = useState<string | null>(null);

  function clearError() {
    setError(null);
  }

  function handleUnauthorized() {
    clearStoredAuth();
    setSession(null);
    setHabits([]);
    setEntries([]);
    setManifestations([]);
    setInspiration(null);
  }

  async function withAuthError<T>(fn: () => Promise<T>): Promise<T> {
    try {
      return await fn();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleUnauthorized();
      }
      throw err;
    }
  }

  async function loadUserData(token: string) {
    setDataLoading(true);
    try {
      const { from, to } = entryRange();
      const [habitsList, entriesList, manifestationsList, inspirationData] =
        await withAuthError(() =>
          Promise.all([
            habitsApi.listHabits(token),
            entriesApi.listEntries(token, from, to),
            manifestationsApi.listManifestations(token),
            inspirationApi.getInspirationToday(token),
          ]),
        );
      setHabits(habitsList);
      setEntries(entriesList);
      setManifestations(manifestationsList);
      setInspiration(inspirationData);
    } finally {
      setDataLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const stored = getStoredAuth();
      if (!stored?.accessToken) {
        if (!cancelled) {
          setSession(null);
          setReady(true);
        }
        return;
      }

      try {
        const me = await authApi.getMe(stored.accessToken);
        if (cancelled) return;
        const next: StoredAuth = {
          ...stored,
          email: (me.email || stored.email).toLowerCase(),
          userId: me.id,
        };
        setStoredAuth(next);
        setSession(authToSession(next));
        await loadUserData(next.accessToken);
      } catch {
        if (!cancelled) {
          clearStoredAuth();
          setSession(null);
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- bootstrap once on mount
  }, []);

  async function applyAuth(
    res: Awaited<ReturnType<typeof authApi.signIn>>,
  ) {
    const stored = sessionFromAuthResponse(res);
    setStoredAuth(stored);
    setSession(authToSession(stored));
    await loadUserData(stored.accessToken);
  }

  async function signIn(email: string, password: string) {
    clearError();
    const res = await authApi.signIn(email.trim().toLowerCase(), password);
    await applyAuth(res);
  }

  async function signUp(email: string, password: string) {
    clearError();
    const res = await authApi.signUp(email.trim().toLowerCase(), password);
    await applyAuth(res);
  }

  async function signOut() {
    const token = session?.accessToken;
    try {
      if (token) await authApi.signOut(token);
    } catch {
      // ignore
    }
    handleUnauthorized();
  }

  function requireToken() {
    if (!session?.accessToken) {
      throw new ApiError(401, "Not signed in");
    }
    return session.accessToken;
  }

  async function addHabit(name: string, daysOfWeek?: number[]) {
    const token = requireToken();
    const habit = await withAuthError(() =>
      habitsApi.createHabit(token, name, daysOfWeek ?? [0, 1, 2, 3, 4, 5, 6]),
    );
    setHabits((prev) => [...prev, habit]);
  }

  async function editHabit(
    id: string,
    patch: Partial<Pick<Habit, "name" | "daysOfWeek" | "archived">>,
  ) {
    const token = requireToken();
    const updated = await withAuthError(() =>
      habitsApi.updateHabit(token, id, patch),
    );
    setHabits((prev) => prev.map((h) => (h.id === id ? updated : h)));
  }

  async function removeHabit(id: string) {
    const token = requireToken();
    await withAuthError(() => habitsApi.deleteHabit(token, id));
    setHabits((prev) => prev.filter((h) => h.id !== id));
    setEntries((prev) => prev.filter((e) => e.habitId !== id));
  }

  async function setStatus(
    habitId: string,
    dateKey: string,
    status: HabitStatus | null,
  ) {
    const token = requireToken();
    const result = await withAuthError(() =>
      entriesApi.upsertEntry(token, habitId, dateKey, status),
    );
    setEntries((prev) => {
      const without = prev.filter(
        (e) => !(e.habitId === habitId && e.date === dateKey),
      );
      if (!result) return without;
      return [...without, result];
    });
  }

  async function cycleStatus(habitId: string, dateKey: string) {
    const existing = getEntry(entries, habitId, dateKey);
    const cycled = cycleEntryStatus(entries, habitId, dateKey);
    if (!cycled) return;
    let nextStatus: HabitStatus | null = null;
    if (!existing) nextStatus = "done";
    else if (existing.status === "done") nextStatus = "not_done";
    else nextStatus = null;
    await setStatus(habitId, dateKey, nextStatus);
  }

  async function refreshInspirationForToken(token: string) {
    try {
      const insp = await inspirationApi.getInspirationToday(token);
      setInspiration(insp);
    } catch {
      // ignore banner refresh failures
    }
  }

  async function addManifestation(text: string) {
    const token = requireToken();
    const item = await withAuthError(() =>
      manifestationsApi.createManifestation(token, text.trim()),
    );
    setManifestations((prev) => [...prev, item]);
    await refreshInspirationForToken(token);
  }

  async function editManifestation(id: string, text: string) {
    const token = requireToken();
    const item = await withAuthError(() =>
      manifestationsApi.updateManifestation(token, id, text.trim()),
    );
    setManifestations((prev) => prev.map((m) => (m.id === id ? item : m)));
    await refreshInspirationForToken(token);
  }

  async function removeManifestation(id: string) {
    const token = requireToken();
    await withAuthError(() =>
      manifestationsApi.deleteManifestation(token, id),
    );
    setManifestations((prev) => prev.filter((m) => m.id !== id));
    await refreshInspirationForToken(token);
  }

  async function refreshInspiration() {
    const token = requireToken();
    const insp = await withAuthError(() =>
      inspirationApi.getInspirationToday(token),
    );
    setInspiration(insp);
  }

  const value: HabitStoreValue = {
    ready,
    dataLoading,
    session,
    habits,
    entries,
    manifestations,
    inspiration,
    error,
    clearError,
    signIn,
    signUp,
    signOut,
    addHabit,
    editHabit,
    removeHabit,
    cycleStatus,
    setStatus,
    addManifestation,
    editManifestation,
    removeManifestation,
    refreshInspiration,
  };

  return (
    <HabitStoreContext.Provider value={value}>
      {children}
    </HabitStoreContext.Provider>
  );
}

export function useHabitStore() {
  const ctx = useContext(HabitStoreContext);
  if (!ctx) {
    throw new Error("useHabitStore must be used within HabitStoreProvider");
  }
  return ctx;
}
