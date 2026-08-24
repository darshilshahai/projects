import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { APP_NAME } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  showTagline?: boolean;
}

export function Logo({ className, showTagline = false }: LogoProps) {
  return (
    <Link href="/" className={cn("inline-flex items-center gap-3", className)}>
      <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-white shadow-sm">
        <ShieldCheck className="h-5 w-5" strokeWidth={2.2} />
      </span>
      <span>
        <span className="block text-base font-semibold tracking-tight text-foreground">
          {APP_NAME}
        </span>
        {showTagline ? (
          <span className="block text-xs text-muted">
            Healthcare Fraud Intelligence
          </span>
        ) : null}
      </span>
    </Link>
  );
}
