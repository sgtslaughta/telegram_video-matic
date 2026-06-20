import { Palette, Check } from 'lucide-react'
import { useAccent } from '@/hooks/useAccent'
import { ACCENTS } from '@/lib/accent'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

export default function AccentPicker() {
  const { accent, setAccent } = useAccent()
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Accent color">
          <Palette className="h-5 w-5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-56">
        <p className="mb-2 text-sm font-medium">Accent color</p>
        <div className="grid grid-cols-2 gap-2">
          {ACCENTS.map((a) => (
            <button
              key={a.name}
              onClick={() => setAccent(a.name)}
              className="flex items-center gap-2 rounded-md border border-border px-2 py-1.5 text-xs hover:bg-muted"
            >
              <span className="h-4 w-4 rounded-full" style={{ backgroundColor: a.swatch }} />
              {a.label}
              {accent === a.name && <Check className="ml-auto h-3 w-3" />}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
