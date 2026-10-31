import { Input } from '@/components/ui/input'
import { Field, Section, ToggleRow, type SectionProps } from './Section'

export function RetentionSection({ s, update }: SectionProps) {
  return (
    <Section title="Retention" description="When old downloads are cleaned up.">
      <ToggleRow id="keep" label="Keep forever" hint="Never delete this subscription's files automatically."
        checked={s.keep} onChange={(c) => update('keep', c)} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Delete after (days)" htmlFor="retention" hint="Leave empty to use the global setting">
          <Input id="retention" type="number" min={1} disabled={s.keep} value={s.retentionDays ?? ''} placeholder="Global setting"
            onChange={(e) => update('retentionDays', e.target.value ? Math.max(1, parseInt(e.target.value)) : null)} />
        </Field>
        <Field label="Size cap (GB)" htmlFor="maxGb" hint="Oldest files are deleted past this. Empty means unlimited.">
          <Input id="maxGb" type="number" min={1} value={s.maxTotalGb ?? ''} placeholder="Unlimited"
            onChange={(e) => update('maxTotalGb', e.target.value ? Math.max(1, parseInt(e.target.value)) : null)} />
        </Field>
      </div>
    </Section>
  )
}
