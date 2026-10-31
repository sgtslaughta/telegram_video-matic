# UI design system (1.8)

Ops dashboard: dense, calm, greyscale surfaces. Violet (`brand`) marks
interaction and focus; green/amber/red (`ok`/`warn`/`err`) mark status only.

## Tokens (Tailwind classes)
- Surfaces: `bg-background` page, `bg-card` panels, `border-border` lines, `bg-muted` wells.
- Text: `text-foreground`, `text-muted-foreground`. Sizes: 20px page title, 13px body/UI,
  12px meta, 11px badges. Numbers use tabular figures (global).
- Brand: `text-brand`, `bg-brand/10` selected, `bg-primary` primary buttons. Links: `text-brand hover:underline`.
- Status: `bg-ok`/`bg-warn`/`bg-err` dots, `bg-err/10` banners. Never use brand for status.
- Radius: `rounded-md` controls, `rounded-lg` panels. No shadows except popovers.
- Motion: `transition-colors` on hover only (150ms global ease). No entrance animations.

## Building blocks
- `Page`, `PageHeader` (`@/components/shared/PageHeader`): every page starts with these.
- Panel = `section.rounded-lg.border.bg-card` with an `h-11` header row (`text-[13px] font-semibold`).
- Tables: full-width, `text-[13px]`, header row `text-[12px] text-muted-foreground`, rows `h-10`,
  `hover:bg-accent/60`, numbers right-aligned. Selection checkbox column first.
- `Sparkline`, `StatTile` (`@/components/shared/Sparkline`) for any trend.
- Times: `relTime()` with `title={absTime()}`; sizes `formatBytes`; durations `formatDuration` (`@/lib/format`).
- Actions: `withToast()` from `@/lib/toast` — success names the action ("Retried 3 downloads"),
  errors show the server detail, reversible actions pass `undo` instead of a confirm dialog.
- Loading: `Skeleton` shaped like the final layout. Empty: one sentence saying what to do next.

## Copy
Sentence case. Name things by what users see ("Downloads", not "jobs"). Buttons say the
action ("Retry download"). No ALL CAPS labels, no exclamation marks, no "Submit".

## Keyboard
`⌘K` palette, `g` + key to switch pages, `/` focuses the page search, `j`/`k` move in lists,
`Enter` opens, `e` edits where relevant.
