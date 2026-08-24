"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useHabitStore } from "@/context/habit-store";
import { ApiError } from "@/lib/api/client";

type AuthFormProps = {
  mode: "sign-in" | "sign-up";
};

export function AuthForm({ mode }: AuthFormProps) {
  const { ready, session, signIn, signUp } = useHabitStore();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (ready && session) {
      router.replace("/today");
    }
  }, [ready, session, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!email.trim() || !email.includes("@")) {
      setError("Enter a valid email.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);
    try {
      if (mode === "sign-in") await signIn(email, password);
      else await signUp(email, password);
      router.push("/today");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Something went wrong";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  const title = mode === "sign-in" ? "Welcome back" : "Create account";
  const subtitle =
    mode === "sign-in"
      ? "Sign in to continue tracking your habits."
      : "Start building consistency today.";
  const cta = mode === "sign-in" ? "Sign in" : "Sign up";
  const alt =
    mode === "sign-in" ? (
      <>
        No account?{" "}
        <Link
          href="/sign-up"
          className="text-foreground underline-offset-4 hover:underline"
        >
          Sign up
        </Link>
      </>
    ) : (
      <>
        Already have an account?{" "}
        <Link
          href="/sign-in"
          className="text-foreground underline-offset-4 hover:underline"
        >
          Sign in
        </Link>
      </>
    );

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div
        className="absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -20%, #1e3a5f55, transparent), radial-gradient(ellipse 60% 40% at 100% 100%, #16161a, transparent)",
        }}
      />
      <div className="animate-fade-up w-full max-w-sm">
        <p className="mb-8 text-center text-lg font-medium tracking-tight">
          Habit Tracker
        </p>
        <h1 className="text-2xl font-medium tracking-tight">{title}</h1>
        <p className="mt-2 text-sm text-muted">{subtitle}</p>
        <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs text-muted">Email</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none transition focus:border-accent"
              placeholder="you@example.com"
              disabled={submitting}
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs text-muted">Password</span>
            <input
              type="password"
              autoComplete={
                mode === "sign-in" ? "current-password" : "new-password"
              }
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none transition focus:border-accent"
              placeholder="••••••••"
              disabled={submitting}
            />
          </label>
          {error && <p className="text-sm text-danger">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-60"
          >
            {submitting ? "Please wait…" : cta}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">{alt}</p>
      </div>
    </div>
  );
}
