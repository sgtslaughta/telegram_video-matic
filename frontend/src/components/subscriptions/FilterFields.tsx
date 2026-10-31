import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { Field, type SectionProps } from './Section'

type Props = SectionProps & { regexValid: boolean; regexError?: string | null; serverError?: string | null }

function numOrNull(v: string): number | null {
  return v === '' ? null : Math.max(0, Number(v))
}

function RegexTester({ s, valid }: { s: SectionProps['s']; valid: boolean }) {
  const [str, setStr] = useState('')
  let m: RegExpMatchArray | null = null
  if (s.filterRegex && valid && str) {
    try { m = str.match(new RegExp(s.filterRegex, 'i')) } catch { m = null }
  }
  const exclude = s.filterMode === 'exclude'
  return (
    <Field label="Test a string" htmlFor="regexTest" hint={!s.filterRegex && str ? 'Enter a pattern above to test it.' : undefined}>
      <Input id="regexTest" value={str} onChange={(e) => setStr(e.target.value)} placeholder="Paste a filename or caption" className="font-mono text-[12px]" />
      {str && valid && s.filterRegex && (
        <p className={cn('text-[12px]', m ? 'text-ok' : 'text-warn')}>
          {m
            ? `Matches "${m[0]}" at position ${m.index}, ${exclude ? 'so it would be skipped' : 'so it would download'}.`
            : `No match, so it would ${exclude ? 'download' : 'be skipped'}.`}
        </p>
      )}
    </Field>
  )
}

export function FilterFields({ s, update, regexValid, regexError, serverError }: Props) {
  const err = regexError || serverError
  return (
    <>
      <div role="radiogroup" aria-label="Filter mode" className="flex w-fit rounded-md border border-border p-0.5 text-[12px]">
        {(['include', 'exclude'] as const).map((mode) => (
          <button key={mode} type="button" role="radio" aria-checked={s.filterMode === mode} onClick={() => update('filterMode', mode)}
            className={cn('rounded px-3 py-1 transition-colors', s.filterMode === mode ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:text-foreground')}>
            {mode === 'include' ? 'Only matching' : 'All except matching'}
          </button>
        ))}
      </div>

      <Field label="Filter regex" htmlFor="regex"
        hint="Case-insensitive pattern matched against file name and caption. Leave empty to match everything.">
        <Textarea id="regex" value={s.filterRegex} onChange={(e) => update('filterRegex', e.target.value)}
          placeholder={'e.g. \\.mkv$  or  (final|semi)'} className={cn('font-mono text-[12px]', err && 'border-err')} rows={2} />
        {s.filterRegex && (err
          ? <p role="alert" className="text-[12px] text-err">✗ {err}</p>
          : regexValid && <p className="text-[12px] text-ok">✓ Valid pattern</p>)}
      </Field>

      <RegexTester s={s} valid={regexValid} />

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Minimum size (MB)" htmlFor="minSize">
          <Input id="minSize" type="number" min={0} value={s.minSizeMb ?? ''} placeholder="No minimum"
            onChange={(e) => update('minSizeMb', numOrNull(e.target.value))} />
        </Field>
        <Field label="Maximum size (MB)" htmlFor="maxSize">
          <Input id="maxSize" type="number" min={0} value={s.maxSizeMb ?? ''} placeholder="No maximum"
            onChange={(e) => update('maxSizeMb', numOrNull(e.target.value))} />
        </Field>
      </div>
    </>
  )
}
