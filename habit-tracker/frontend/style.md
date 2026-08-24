# Habit Tracker — Frontend Style Guide

Dark-only, minimal UI. Source of truth for tokens: [`app/globals.css`](app/globals.css).

---

## Theme

| Rule | Value |
|------|--------|
| Mode | Dark only (`color-scheme: dark`) |
| Atmosphere | Near-black base + subtle fixed grain overlay (`opacity: 0.035`) |
| Accent | Cool blue (not purple) |
| Density | Compact, functional — progress grids over card chrome |

---

## Color tokens

Defined on `:root` and mapped into Tailwind via `@theme inline`.

| Token | Hex | Tailwind | Usage |
|-------|-----|----------|--------|
| `--background` | `#0c0c0e` | `bg-background` | Page background |
| `--foreground` | `#ececef` | `text-foreground` | Primary text |
| `--surface` | `#16161a` | `bg-surface` | Panels, nav active, inputs area |
| `--surface-hover` | `#1e1e24` | `bg-surface-hover` / `hover:bg-surface-hover` | Hover rows / secondary actions |
| `--border` | `#2a2a32` | `border-border` | Dividers, outlines (`border-border/60`, `/70` common) |
| `--muted` | `#8b8b96` | `text-muted` | Secondary copy, labels, hints |
| `--accent` | `#3b82f6` | `bg-accent` / `text-accent` | Primary CTA, done cells, focus rings |
| `--accent-soft` | `#1e3a5f` | `bg-accent-soft` | Soft blue washes (hero/banner gradients) |
| `--danger` | `#ef4444` | `text-danger` / `bg-danger/*` | Errors, not-done control, delete |
| `--success` | `#22c55e` | `text-success` / `bg-success/*` | Done check control |

### Habit grid cells

| Token | Hex | Tailwind | Meaning |
|-------|-----|----------|---------|
| `--cell-done` | `#3b82f6` | `bg-cell-done` | Completed |
| `--cell-miss` | `#2e2e36` | `bg-cell-miss` | Not done |
| `--cell-pending` | `#3a3a44` | `bg-cell-pending` | Today, unset |
| `--cell-empty` | `#232328` | `bg-cell-empty` | Empty / off-schedule filler |

---

## Typography

| Role | Family | CSS variable | Notes |
|------|--------|--------------|--------|
| UI / body | **Outfit** | `--font-outfit` → `--font-sans` | Loaded via `next/font` in [`app/layout.tsx`](app/layout.tsx) |
| Numbers / grids | **IBM Plex Mono** | `--font-ibm-plex-mono` → `--font-mono` | Weights 400, 500 — day numbers, streaks |

### Type scale (common patterns)

| Element | Classes |
|---------|---------|
| Page title | `text-2xl font-medium tracking-tight` |
| Section title | `text-sm font-medium` |
| Body / support | `text-sm text-muted` |
| Eyebrow / label | `text-[11px] font-medium uppercase tracking-[0.14em] text-muted` |
| Form label | `text-xs text-muted` |
| Mono meta | `font-mono text-xs text-muted` |
| Quote | `text-base sm:text-lg leading-relaxed text-foreground/95` |

---

## Layout

| Rule | Value |
|------|--------|
| Content max width | `max-w-5xl` |
| Page padding | `px-4 sm:px-6`, vertical `py-8` |
| App shell | Sticky top nav + main column |
| Mobile nav | Bottom tab row under header (`sm:hidden`) |

---

## Surfaces & radius

| Pattern | Classes |
|---------|---------|
| Soft panel | `rounded-xl border border-border/70 bg-surface/40` (or `/50`) |
| Banner / hero block | `rounded-2xl border border-border/60` + radial gradients |
| Empty state | `rounded-xl border border-dashed border-border` |
| Inputs | `rounded-lg border border-border bg-background` (or `bg-surface`) |
| Primary button | `rounded-lg bg-accent … text-white hover:brightness-110` |
| Ghost / text button | `text-muted hover:text-foreground` |
| Focus | `focus:border-accent` / `hover:ring-1 hover:ring-accent/60` on grid cells |

Prefer low opacity borders (`/50`–`/70`) over heavy shadows. No multi-layer glow.

---

## Components (visual)

### Check-in controls
- Done: green check — `text-success`, selected `bg-success/20 ring-1 ring-success/40`
- Not done: red X — `text-danger`, selected `bg-danger/20 ring-1 ring-danger/40`
- Hit target ~ `h-10 w-10`

### Progress grids
- Monthly matrix: small rounded cells `rounded-[3px]`, accent ring for today
- Contribution squares: `h-[11px] w-[11px] rounded-[2px]`
- Horizontal scroll on small screens

### Inspiration banner
- Dark radial wash using `#1e3a5f` / surface tones
- Accent dots for manifestation lines

---

## Motion

| Class | Behavior |
|-------|----------|
| `.animate-fade-up` | Opacity + 6px rise, `0.35s ease-out` |
| `.animate-cell-pop` | Brief scale pop, `0.2s ease-out` |

Use sparingly for page enter and cell feedback — not decorative noise.

---

## Tailwind usage

Prefer semantic token classes over raw hex:

```tsx
// Good
className="bg-surface text-foreground border-border"

// Avoid scattering
className="bg-[#16161a] text-[#ececef]"
```

Opacity modifiers on tokens are part of the system: `border-border/60`, `bg-surface/40`, `text-foreground/80`.

---

## Do / Don’t

**Do**
- Keep forced dark mode
- Use Outfit + IBM Plex Mono
- Use blue accent for “done” / primary actions
- Keep UI minimal and dense for tracking

**Don’t**
- Add light mode without a deliberate redesign
- Default to purple / indigo gradients or glow aesthetics
- Overuse cards, pills, or multi-shadow stacks
- Replace brand fonts with Inter / system-only stacks for marketing surfaces
