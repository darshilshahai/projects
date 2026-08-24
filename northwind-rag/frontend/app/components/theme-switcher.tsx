"use client";

import { useTheme } from "./theme-provider";

export function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      className="cursor-pointer rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-muted hover:text-foreground"
    >
      {theme === "dark" ? "Light" : "Dark"}
    </button>
  );
}
