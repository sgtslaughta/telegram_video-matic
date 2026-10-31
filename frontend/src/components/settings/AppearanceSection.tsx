import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'
import AccentPicker from '@/components/AccentPicker'
import { Field, SettingsSection } from './SettingsSection'

const THEMES = [['light', 'Light'], ['dark', 'Dark'], ['system', 'System']] as const

export function AppearanceSection() {
  const { theme, setTheme } = useTheme()
  return (
    <SettingsSection id="appearance" title="Appearance" description="Applies immediately and is remembered on this device.">
      <Field id="theme" label="Theme">
        <div role="radiogroup" aria-label="Theme" id="theme" className="inline-flex rounded-md border border-border p-0.5 text-[13px]">
          {THEMES.map(([v, l]) => (
            <button key={v} role="radio" aria-checked={theme === v} onClick={() => setTheme(v)}
              className={cn('rounded px-3 py-1 transition-colors', theme === v ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:text-foreground')}>
              {l}
            </button>
          ))}
        </div>
      </Field>
      <Field id="accent" label="Accent color">
        <AccentPicker />
      </Field>
    </SettingsSection>
  )
}
