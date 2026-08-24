"use client";

import { site } from "@/data/site";
import { useLocalTime } from "@/hooks/use-local-time";

export function SiteFooter({ compact = false }: { compact?: boolean }) {
  const time = useLocalTime();
  const year = new Date().getFullYear();

  return (
    <footer className="site-colophon" style={compact ? { marginTop: 48 } : undefined}>
      <p>
        <small>Edition</small>
        {year} © Darshil Shah
      </p>
      <p>
        <small>Local</small>
        <span suppressHydrationWarning>{time} IST · India</span>
      </p>
      <p>
        <small>Links</small>
        <a href={site.github} target="_blank" rel="noopener noreferrer">GitHub</a>
        {" · "}
        <a href={site.linkedin} target="_blank" rel="noopener noreferrer">LinkedIn</a>
      </p>
    </footer>
  );
}
