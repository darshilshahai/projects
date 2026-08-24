"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useHabitStore } from "@/context/habit-store";

export default function HomePage() {
  const { ready, session } = useHabitStore();
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    router.replace(session ? "/today" : "/sign-in");
  }, [ready, session, router]);

  return (
    <div className="flex min-h-screen items-center justify-center text-sm text-muted">
      Loading…
    </div>
  );
}
