// Accent presets. Each maps to the shadcn --primary/--ring CSS vars (HSL triples).
// White foreground works on every colored accent in both light and dark themes.
export type AccentName = 'telegram' | 'violet' | 'green' | 'rose' | 'orange' | 'amber'

export interface Accent {
  name: AccentName
  label: string
  swatch: string // hex, for the picker dot
  primary: string // HSL triple for --primary / --ring
}

export const ACCENTS: Accent[] = [
  { name: 'telegram', label: 'Telegram', swatch: '#229ed9', primary: '201 73% 49%' },
  { name: 'violet', label: 'Violet', swatch: '#7c3aed', primary: '262 83% 58%' },
  { name: 'green', label: 'Green', swatch: '#16a34a', primary: '142 71% 45%' },
  { name: 'rose', label: 'Rose', swatch: '#e11d48', primary: '347 77% 50%' },
  { name: 'orange', label: 'Orange', swatch: '#f97316', primary: '25 95% 53%' },
  { name: 'amber', label: 'Amber', swatch: '#f59e0b', primary: '38 92% 50%' },
]

export const DEFAULT_ACCENT: AccentName = 'telegram'

export function applyAccent(name: AccentName): void {
  const a = ACCENTS.find((x) => x.name === name) ?? ACCENTS[0]
  const root = document.documentElement
  root.style.setProperty('--primary', a.primary)
  root.style.setProperty('--primary-foreground', '0 0% 100%')
  root.style.setProperty('--ring', a.primary)
}
