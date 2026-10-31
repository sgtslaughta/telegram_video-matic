// Accent presets. Each maps to the shadcn --primary/--ring CSS vars (HSL triples).
// White foreground works on every colored accent in both light and dark themes.
export type AccentName = 'violet' | 'graphite' | 'telegram'

export interface Accent {
  name: AccentName
  label: string
  swatch: string // hex, for the picker dot
  primary: string // HSL triple for --primary / --ring
}

export const ACCENTS: Accent[] = [
  { name: 'violet', label: 'Violet', swatch: '#7c5cff', primary: '' },
  { name: 'graphite', label: 'Graphite', swatch: '#18181b', primary: 'var(--foreground)' },
  { name: 'telegram', label: 'Telegram', swatch: '#229ed9', primary: '201 73% 49%' },
]

export const DEFAULT_ACCENT: AccentName = 'violet'

export function applyAccent(name: AccentName): void {
  const a = ACCENTS.find((x) => x.name === name) ?? ACCENTS[0]
  const root = document.documentElement
  if (!a.primary) {
    // Default violet: the theme tokens already define light/dark variants.
    for (const v of ['--primary', '--primary-foreground', '--ring', '--brand']) root.style.removeProperty(v)
    return
  }
  root.style.setProperty('--primary', a.primary)
  root.style.setProperty('--brand', a.primary)
  root.style.setProperty('--ring', a.primary)
  root.style.setProperty('--primary-foreground', a.name === 'graphite' ? 'var(--background)' : '0 0% 100%')
}
