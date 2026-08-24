"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useHabitStore } from "@/context/habit-store";

const links = [
  { href: "/today", label: "Today" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/habits", label: "Habits" },
  { href: "/manifestations", label: "Manifest" },
];

export function Nav() {
  const pathname = usePathname();
  const { session, signOut } = useHabitStore();

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <Link
            href="/today"
            className="font-medium tracking-tight text-foreground"
          >
            Habit Tracker
          </Link>
          <nav className="hidden items-center gap-1 sm:flex">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "bg-surface text-foreground"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {session && (
            <span className="hidden max-w-[140px] truncate text-xs text-muted sm:inline">
              {session.email}
            </span>
          )}
          <button
            type="button"
            onClick={signOut}
            className="text-xs text-muted transition-colors hover:text-foreground"
          >
            Sign out
          </button>
        </div>
      </div>
      <nav className="flex border-t border-border/60 sm:hidden">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex-1 py-2.5 text-center text-sm transition-colors ${
                active
                  ? "text-foreground"
                  : "text-muted"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
