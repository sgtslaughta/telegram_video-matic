import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { withToast } from '@/lib/toast'
import { notifications } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { NotificationTargets } from './NotificationTargets'
import { SettingsSection } from './SettingsSection'
import type * as T from '@/lib/types'

const HOURS = Array.from({ length: 24 }, (_, h) => h)
const hh = (h: number) => `${String(h).padStart(2, '0')}:00`

function HourSelect({ id, label, value, onChange }: {
  id: string
  label: string
  value: number
  onChange: (v: number) => void
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-[13px]">{label}</Label>
      <Select value={String(value)} onValueChange={(v) => onChange(Number(v))}>
        <SelectTrigger id={id} className="h-9 w-28 text-[13px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {HOURS.map((h) => (
            <SelectItem key={h} value={String(h)}>{hh(h)}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

const sub = 'text-[13px] font-semibold'
const help = 'text-[12px] text-muted-foreground'
const field = 'h-9 text-[13px]'

function OptionsForm({ initial }: { initial: T.NotificationOptions }) {
  const qc = useQueryClient()
  const [opts, setOpts] = useState(initial)
  const dirty = JSON.stringify(opts) !== JSON.stringify(initial)
  const save = useMutation({
    mutationFn: () => notifications.saveOptions(opts),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
  const setQuiet = (p: Partial<T.NotificationOptions['quiet']>) =>
    setOpts({ ...opts, quiet: { ...opts.quiet, ...p } })

  return (
    <div className="space-y-4">
      <h3 className={sub}>Options</h3>
      <div className="flex items-center gap-2">
        <Switch id="quiet-enabled" checked={opts.quiet.enabled} onCheckedChange={(c) => setQuiet({ enabled: c })} />
        <Label htmlFor="quiet-enabled" className="text-[13px]">Quiet hours</Label>
      </div>
      <div className="flex gap-4">
        <HourSelect id="quiet-start" label="Start" value={opts.quiet.start} onChange={(v) => setQuiet({ start: v })} />
        <HourSelect id="quiet-end" label="End" value={opts.quiet.end} onChange={(v) => setQuiet({ end: v })} />
      </div>
      <p className={help}>
        Arrivals are held and sent as one summary when quiet hours end. Errors still send immediately.
      </p>
      <div className="space-y-1.5">
        <Label htmlFor="disk-low" className="text-[13px]">Disk low threshold (%)</Label>
        <Input id="disk-low" type="number" min={50} max={100} className={`${field} max-w-xs`} value={opts.disk_low_pct}
          onChange={(e) => setOpts({ ...opts, disk_low_pct: Number(e.target.value) })} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="public-url" className="text-[13px]">Public URL</Label>
        <Input id="public-url" className={`${field} max-w-md`} value={opts.public_url}
          onChange={(e) => setOpts({ ...opts, public_url: e.target.value })} />
        <p className={help}>Used for links in notifications, e.g. http://192.168.1.96:8000</p>
      </div>
      {dirty && (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => withToast(() => save.mutateAsync(), { success: 'Notification options saved' })} disabled={save.isPending}>Save changes</Button>
        </div>
      )}
    </div>
  )
}

function JellyfinForm({ initial }: { initial: T.NotificationJellyfin }) {
  const qc = useQueryClient()
  const [url, setUrl] = useState(initial.url)
  const [libraryId, setLibraryId] = useState(initial.library_id)
  const [apiKey, setApiKey] = useState('')
  const dirty = url !== initial.url || libraryId !== initial.library_id || apiKey !== ''
  const save = useMutation({
    mutationFn: () => notifications.saveJellyfin({ url, library_id: libraryId, ...(apiKey ? { api_key: apiKey } : {}) }),
    onSuccess: () => { setApiKey(''); qc.invalidateQueries({ queryKey: ['notifications'] }) },
  })
  const test = useMutation({ mutationFn: () => notifications.testJellyfin() })

  return (
    <div className="space-y-4">
      <h3 className={sub}>Jellyfin</h3>
      <div className="space-y-1.5">
        <Label htmlFor="jf-url" className="text-[13px]">URL</Label>
        <Input id="jf-url" className={`${field} max-w-md`} value={url} onChange={(e) => setUrl(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="jf-lib" className="text-[13px]">Library ID</Label>
        <Input id="jf-lib" className={`${field} max-w-md`} value={libraryId} onChange={(e) => setLibraryId(e.target.value)} />
        <p className={help}>Leave empty to refresh all libraries.</p>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="jf-key" className="text-[13px]">API key</Label>
        <Input id="jf-key" type="password" className={`${field} max-w-md`} value={apiKey}
          placeholder={initial.api_key_set ? 'Saved, leave empty to keep' : ''} onChange={(e) => setApiKey(e.target.value)} />
      </div>
      <div className="flex justify-end gap-2">
        <Button size="sm" variant="outline" disabled={test.isPending}
          onClick={() => withToast(() => test.mutateAsync(), { success: 'Jellyfin refresh started' })}>Test refresh</Button>
        {dirty && (
          <Button size="sm" disabled={save.isPending} onClick={() => withToast(() => save.mutateAsync(), { success: 'Jellyfin settings saved' })}>Save changes</Button>
        )}
      </div>
    </div>
  )
}

export function NotificationsSettings() {
  const { data } = useQuery({ queryKey: ['notifications'], queryFn: notifications.get })

  return (
    <SettingsSection id="notifications" title="Notifications"
      description="Send alerts through Apprise and refresh Jellyfin after new downloads.">
      {data ? (
        <div className="divide-y divide-border [&>*]:py-5 [&>:first-child]:pt-0 [&>:last-child]:pb-0">
          <NotificationTargets triggers={data.triggers} targets={data.targets} />
          <OptionsForm key={JSON.stringify(data.options)} initial={data.options} />
          <JellyfinForm initial={data.jellyfin} />
        </div>
      ) : (
        <p className="text-[13px] text-muted-foreground">Loading notifications…</p>
      )}
    </SettingsSection>
  )
}
