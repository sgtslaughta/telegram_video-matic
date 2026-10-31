import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'
import { withToast } from '@/lib/toast'
import type * as T from '@/lib/types'
import { Field, SettingsSection, inputCls } from './SettingsSection'

type Key = 'poll_interval_sec' | 'max_concurrent_downloads' | 'retention_days' | 'retention_disk_pct'

/** Draft of a group of numeric settings; dirty when it differs from the server. */
function useGroup(keys: Key[], saved: string) {
  const { data } = useSettings()
  const update = useUpdateSettings()
  const base = Object.fromEntries(keys.map((k) => [k, data?.find((s) => s.key === k)?.value ?? '']))
  const [draft, setDraft] = useState<Record<string, string>>(base)
  const dirty = keys.some((k) => draft[k] !== base[k])
  const save = async () => {
    const patch: T.SettingPatchRequest = {}
    keys.forEach((k) => { patch[k] = draft[k] === '' ? null : Number(draft[k]) })
    await withToast(() => update.mutateAsync(patch), { success: saved })
  }
  return { draft, set: (k: Key, v: string) => setDraft((d) => ({ ...d, [k]: v })), dirty, save, saving: update.isPending }
}

export function GeneralSection() {
  const g = useGroup(['poll_interval_sec', 'max_concurrent_downloads'], 'General settings saved')
  return (
    <SettingsSection id="general" title="General" description="How often the app checks for new videos and how many it downloads at once."
      dirty={g.dirty} saving={g.saving} onSave={g.save}>
      <Field id="poll" label="Poll interval (seconds)" help="How often subscriptions are scanned for new videos.">
        <Input id="poll" type="number" min={1} className={inputCls} value={g.draft.poll_interval_sec} onChange={(e) => g.set('poll_interval_sec', e.target.value)} />
      </Field>
      <Field id="max-dl" label="Concurrent downloads" help="Higher is faster but uses more bandwidth and CPU.">
        <Input id="max-dl" type="number" min={1} className={inputCls} value={g.draft.max_concurrent_downloads} onChange={(e) => g.set('max_concurrent_downloads', e.target.value)} />
      </Field>
    </SettingsSection>
  )
}

export function CleanupSection() {
  const g = useGroup(['retention_days', 'retention_disk_pct'], 'Cleanup settings saved')
  return (
    <SettingsSection id="cleanup" title="Cleanup" description="Automatic deletion keeps the disk from filling up."
      dirty={g.dirty} saving={g.saving} onSave={g.save}>
      <Field id="retention" label="Retention (days)"
        help="Videos are deleted this many days after the match date. Pinned videos and subscriptions are kept.">
        <Input id="retention" type="number" min={0} className={inputCls} value={g.draft.retention_days} onChange={(e) => g.set('retention_days', e.target.value)} />
      </Field>
      <Field id="retention-pct" label="Disk usage limit (%)" help="When the disk is this full, the oldest videos are deleted until it is back under.">
        <Input id="retention-pct" type="number" min={1} max={100} className={inputCls} value={g.draft.retention_disk_pct} onChange={(e) => g.set('retention_disk_pct', e.target.value)} />
      </Field>
    </SettingsSection>
  )
}
