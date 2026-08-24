"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { Brand } from "@/components/shared";
import {
  EVALUATION_PATH,
  NAV_LINKS,
  WORKSPACE_PATH,
} from "@/lib/constants/site";
import { cn } from "@/lib/utils/cn";

export function Navbar() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-border-subtle bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-6 md:px-10">
        <Brand />

        <nav
          className="hidden items-center gap-6 font-mono text-[10px] tracking-[0.14em] text-muted uppercase md:flex"
          aria-label="Primary"
        >
          {NAV_LINKS.map((link) => (
            <NavItem
              key={link.label}
              link={link}
              active={
                link.href === WORKSPACE_PATH
                  ? pathname === WORKSPACE_PATH
                  : link.href === EVALUATION_PATH
                    ? pathname === EVALUATION_PATH
                    : false
              }
            />
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href={WORKSPACE_PATH}
            className="landing-cta landing-cta-primary hidden sm:inline-flex"
          >
            START ANALYZING ↘
          </Link>

          <button
            type="button"
            className="inline-flex items-center justify-center border border-border-subtle p-2 text-muted transition-colors duration-150 hover:border-border hover:text-foreground md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close navigation menu" : "Open navigation menu"}
            onClick={() => setOpen((current) => !current)}
          >
            {open ? (
              <X className="size-4" aria-hidden="true" />
            ) : (
              <Menu className="size-4" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {open ? (
        <nav
          id="mobile-nav"
          className="border-t border-border-subtle px-6 py-4 md:hidden"
          aria-label="Mobile"
        >
          <ul className="flex flex-col gap-3 font-mono text-[10px] tracking-[0.14em] text-muted uppercase">
            {NAV_LINKS.map((link) => (
              <li key={link.label}>
                <NavItem
                  link={link}
                  onNavigate={() => setOpen(false)}
                  className="block py-1"
                  active={
                    link.href === WORKSPACE_PATH
                      ? pathname === WORKSPACE_PATH
                      : link.href === EVALUATION_PATH
                        ? pathname === EVALUATION_PATH
                        : false
                  }
                />
              </li>
            ))}
            <li className="pt-2">
              <Link
                href={WORKSPACE_PATH}
                className="landing-cta landing-cta-primary inline-flex w-full justify-center"
                onClick={() => setOpen(false)}
              >
                START ANALYZING ↘
              </Link>
            </li>
          </ul>
        </nav>
      ) : null}
    </header>
  );
}

function NavItem({
  link,
  onNavigate,
  className,
  active = false,
}: {
  link: (typeof NAV_LINKS)[number];
  onNavigate?: () => void;
  className?: string;
  active?: boolean;
}) {
  const isExternal = link.external ?? link.href.startsWith("http");

  const linkClassName = cn(
    "transition-colors duration-150 hover:text-foreground",
    active && "text-accent",
    className,
  );

  if (isExternal) {
    return (
      <a
        href={link.href}
        target="_blank"
        rel="noopener noreferrer"
        className={linkClassName}
        onClick={onNavigate}
      >
        {link.label}
      </a>
    );
  }

  return (
    <Link href={link.href} className={linkClassName} onClick={onNavigate}>
      {link.label}
    </Link>
  );
}
