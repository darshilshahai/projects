"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useHabitStore } from "@/context/habit-store";
import { InspirationBanner } from "@/components/inspiration-banner";
import { Nav } from "@/components/nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { ready, session, dataLoading } = useHabitStore();
  const router = useRouter();

  useEffect(() => {
    if (ready && !session) {
      router.replace("/sign-in");
    }
  }, [ready, session, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted">
        Loading…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted">
        Redirecting…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        <InspirationBanner />
        {dataLoading ? (
          <p className="mb-4 text-sm text-muted">Syncing your habits…</p>
        ) : null}
        {children}
      </main>
    </div>
  );
}
