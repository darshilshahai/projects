"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";

interface AuthLayoutProps {
  mode: "sign-in" | "sign-up";
  children?: React.ReactNode;
}

export function AuthLayout({ mode }: AuthLayoutProps) {
  const router = useRouter();
  const { signIn, signUp } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [organization, setOrganization] = useState("INSURER-001");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const isSignUp = mode === "sign-up";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!email || !password || (isSignUp && !name)) {
      setError("Please fill in all required fields.");
      return;
    }

    const user = {
      name: name || email.split("@")[0],
      email,
      organization,
    };

    if (isSignUp) {
      signUp(user);
    } else {
      signIn(user);
    }

    router.push("/dashboard");
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="grid min-h-screen lg:grid-cols-2">
        <div className="hero-grid relative hidden flex-col justify-between px-10 py-10 lg:flex">
          <Logo showTagline />

          <div className="max-w-md">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
              Healthcare fraud intelligence
            </p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight tracking-tight text-foreground">
              Secure access to grounded investigation tools
            </h1>
            <p className="mt-4 text-base leading-8 text-muted">
              Sign in to query fraud guidelines, claim documents, and compliance
              records with semantic search and cited answers.
            </p>
          </div>

          <div className="rounded-[24px] border border-border bg-card/80 p-5 shadow-[var(--shadow)]">
            <p className="text-sm font-medium text-foreground">
              Example investigation query
            </p>
            <p className="mt-2 text-sm leading-7 text-muted">
              &ldquo;How can repeated billing indicate fraud?&rdquo;
            </p>
          </div>
        </div>

        <div className="flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-md">
            <div className="mb-8 lg:hidden">
              <Logo showTagline />
            </div>

            <div className="rounded-[28px] border border-border bg-card p-8 shadow-[var(--shadow)]">
              <div className="mb-8">
                <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                  {isSignUp ? "Create your workspace" : "Welcome back"}
                </h2>
                <p className="mt-2 text-sm text-muted">
                  {isSignUp
                    ? "Set up access to your fraud investigation dashboard."
                    : "Sign in to continue your investigations."}
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {isSignUp ? (
                  <Input
                    label="Full name"
                    placeholder="Alex Morgan"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    autoComplete="name"
                  />
                ) : null}

                <Input
                  label="Work email"
                  type="email"
                  placeholder="alex@insurer.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                />

                <Input
                  label="Organization ID"
                  placeholder="INSURER-001"
                  value={organization}
                  onChange={(event) => setOrganization(event.target.value)}
                />

                <Input
                  label="Password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete={
                    isSignUp ? "new-password" : "current-password"
                  }
                />

                {error ? (
                  <p className="rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger">
                    {error}
                  </p>
                ) : null}

                <Button type="submit" className="w-full" size="lg">
                  {isSignUp ? "Create account" : "Sign in"}
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-muted">
                {isSignUp ? "Already have an account?" : "Need an account?"}{" "}
                <Link
                  href={isSignUp ? "/sign-in" : "/sign-up"}
                  className="font-medium text-primary hover:text-primary-hover"
                >
                  {isSignUp ? "Sign in" : "Create one"}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
