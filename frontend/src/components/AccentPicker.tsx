import { Check } from 'lucide-react'
import { useAccent } from '@/hooks/useAccent'
import { ACCENTS } from '@/lib/accent'
import { cn } from '@/lib/utils'

export default function AccentPicker() {
  const { accent, setAccent } = useAccent()
  return (
    <div role="radiogroup" aria-label="Accent color" className="flex flex-wrap gap-2">
      {ACCENTS.map((a) => (
        <button key={a.name} role="radio" aria-checked={accent === a.name} onClick={() => setAccent(a.name)}
          className={cn('flex items-center gap-2 rounded-md border px-3 py-1.5 text-[13px] transition-colors',
            accent === a.name ? 'border-brand bg-brand/10 font-medium text-brand' : 'border-border text-muted-foreground hover:text-foreground')}>
          <span className="flex h-4 w-4 items-center justify-center rounded-full border border-border" style={{ backgroundColor: a.swatch }}>
            {accent === a.name && <Check className="h-2.5 w-2.5 text-white" strokeWidth={3} />}
          </span>
          {a.label}
        </button>
      ))}
    </div>
  )
}
