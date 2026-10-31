import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { notifications } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { NotificationTargets } from './NotificationTargets'
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
    <div className="space-y-1">
      <Label htmlFor={id}>{label}</Label>
      <Select value={String(value)} onValueChange={(v) => onChange(Number(v))}>
        <SelectTrigger id={id} className="w-28">
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

function OptionsForm({ initial }: { initial: T.NotificationOptions }) {
  const qc = useQueryClient()
  const [opts, setOpts] = useState(initial)
  useEffect(() => setOpts(initial), [initial])
  const save = useMutation({
    mutationFn: () => notifications.saveOptions(opts),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Options saved')
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const setQuiet = (p: Partial<T.NotificationOptions['quiet']>) =>
    setOpts({ ...opts, quiet: { ...opts.quiet, ...p } })

  return (
    <div className="space-y-4">
      <h3 className="font-medium">Options</h3>
      <div className="flex items-center gap-2">
        <Switch
          id="quiet-enabled"
          checked={opts.quiet.enabled}
          onCheckedChange={(c) => setQuiet({ enabled: c })}
        />
        <Label htmlFor="quiet-enabled">Quiet hours</Label>
      </div>
      <div className="flex gap-4">
        <HourSelect id="quiet-start" label="Start" value={opts.quiet.start} onChange={(v) => setQuiet({ start: v })} />
        <HourSelect id="quiet-end" label="End" value={opts.quiet.end} onChange={(v) => setQuiet({ end: v })} />
      </div>
      <p className="text-xs text-muted-foreground">
        Arrivals are held and sent as one summary when quiet hours end. Errors still send immediately.
      </p>
      <div className="space-y-1">
        <Label htmlFor="disk-low">Disk low threshold (%)</Label>
        <Input
          id="disk-low"
          type="number"
          min={50}
          max={100}
          value={opts.disk_low_pct}
          onChange={(e) => setOpts({ ...opts, disk_low_pct: Number(e.target.value) })}
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="public-url">Public URL</Label>
        <Input
          id="public-url"
          value={opts.public_url}
          onChange={(e) => setOpts({ ...opts, public_url: e.target.value })}
        />
        <p className="text-xs text-muted-foreground">
          Used for links in notifications, e.g. http://192.168.1.96:8000
        </p>
      </div>
      <Button onClick={() => save.mutate()} disabled={save.isPending}>Save options</Button>
    </div>
  )
}

function JellyfinForm({ initial }: { initial: T.NotificationJellyfin }) {
  const qc = useQueryClient()
  const [url, setUrl] = useState(initial.url)
  const [libraryId, setLibraryId] = useState(initial.library_id)
  const [apiKey, setApiKey] = useState('')
  const onError = (e: Error) => toast.error(e.message)
  const save = useMutation({
    mutationFn: () =>
      notifications.saveJellyfin({
        url,
        library_id: libraryId,
        ...(apiKey ? { api_key: apiKey } : {}),
      }),
    onSuccess: () => {
      setApiKey('')
      qc.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Jellyfin saved')
    },
    onError,
  })
  const test = useMutation({
    mutationFn: () => notifications.testJellyfin(),
    onSuccess: () => toast.success('Jellyfin refresh started'),
    onError,
  })

  return (
    <div className="space-y-4">
      <h3 className="font-medium">Jellyfin</h3>
      <div className="space-y-1">
        <Label htmlFor="jf-url">URL</Label>
        <Input id="jf-url" value={url} onChange={(e) => setUrl(e.target.value)} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="jf-lib">Library ID</Label>
        <Input id="jf-lib" value={libraryId} onChange={(e) => setLibraryId(e.target.value)} />
        <p className="text-xs text-muted-foreground">Leave empty to refresh all libraries</p>
      </div>
      <div className="space-y-1">
        <Label htmlFor="jf-key">API key</Label>
        <Input
          id="jf-key"
          type="password"
          value={apiKey}
          placeholder={initial.api_key_set ? 'Saved — leave empty to keep' : ''}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </div>
      <div className="flex gap-2">
        <Button onClick={() => save.mutate()} disabled={save.isPending}>Save Jellyfin</Button>
        <Button variant="outline" onClick={() => test.mutate()} disabled={test.isPending}>
          Test refresh
        </Button>
      </div>
    </div>
  )
}

export function NotificationsSettings() {
  const { data } = useQuery({ queryKey: ['notifications'], queryFn: notifications.get })

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <p className="text-sm text-muted-foreground">
          Send alerts through Apprise and refresh Jellyfin after new downloads.
        </p>
      </CardHeader>
      <CardContent className="space-y-8">
        {data ? (
          <>
            <NotificationTargets triggers={data.triggers} targets={data.targets} />
            <OptionsForm initial={data.options} />
            <JellyfinForm initial={data.jellyfin} />
          </>
        ) : (
          <p className="text-sm text-muted-foreground">Loading notifications...</p>
        )}
      </CardContent>
    </Card>
  )
}
