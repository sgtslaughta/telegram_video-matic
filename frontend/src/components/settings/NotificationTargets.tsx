import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { notifications } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import type * as T from '@/lib/types'

export const TRIGGER_LABELS: Record<string, string> = {
  download_complete: 'Download finished',
  download_failed: 'Download failed',
  telegram: 'Telegram connection lost / restored',
  unmatched: 'Video needs review',
  disk_low: 'Disk space low',
}

const toInput = (t: T.NotificationTarget): T.NotificationTargetInput => ({
  id: t.id,
  name: t.name,
  triggers: t.triggers,
})

function TriggerBoxes({ idPrefix, all, value, onChange }: {
  idPrefix: string
  all: string[]
  value: string[]
  onChange: (v: string[]) => void
}) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-2">
      {all.map((t) => (
        <div key={t} className="flex items-center gap-2">
          <Checkbox
            id={`${idPrefix}-${t}`}
            checked={value.includes(t)}
            onCheckedChange={(c) =>
              onChange(c === true ? [...value, t] : value.filter((x) => x !== t))
            }
          />
          <Label htmlFor={`${idPrefix}-${t}`} className="text-sm font-normal">
            {TRIGGER_LABELS[t] ?? t}
          </Label>
        </div>
      ))}
    </div>
  )
}

export function NotificationTargets({ triggers, targets }: {
  triggers: string[]
  targets: T.NotificationTarget[]
}) {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [newTriggers, setNewTriggers] = useState<string[]>(triggers)
  const [replace, setReplace] = useState<Record<string, string>>({})

  const onError = (e: Error) => toast.error(e.message)

  const save = useMutation({
    mutationFn: (list: T.NotificationTargetInput[]) => notifications.saveTargets(list),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Target saved')
    },
    onError,
  })
  const test = useMutation({
    mutationFn: (body: { id: string } | { url: string }) => notifications.test(body),
    onSuccess: () => toast.success('Test sent'),
    onError,
  })

  const existing = targets.map(toInput)
  const update = (id: string, patch: Partial<T.NotificationTargetInput>) =>
    save.mutate(existing.map((t) => (t.id === id ? { ...t, ...patch } : t)))

  const add = () => {
    save.mutate([...existing, { name, url, triggers: newTriggers }], {
      onSuccess: () => {
        setName('')
        setUrl('')
        setNewTriggers(triggers)
      },
    })
  }

  return (
    <div className="space-y-4">
      <h3 className="font-medium">Targets</h3>
      {targets.length === 0 && (
        <p className="text-sm text-muted-foreground">No targets yet.</p>
      )}
      {targets.map((t) => (
        <div key={t.id} className="space-y-2 rounded-md border p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="font-medium">{t.name}</p>
              <p className="text-xs text-muted-foreground">{t.url_masked}</p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => test.mutate({ id: t.id })}>
                Send test
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => save.mutate(existing.filter((x) => x.id !== t.id))}
              >
                Remove
              </Button>
            </div>
          </div>
          <TriggerBoxes
            idPrefix={`t-${t.id}`}
            all={triggers}
            value={t.triggers}
            onChange={(v) => update(t.id, { triggers: v })}
          />
          <div className="flex items-end gap-2">
            <div className="flex-1 space-y-1">
              <Label htmlFor={`replace-${t.id}`}>Replace URL</Label>
              <Input
                id={`replace-${t.id}`}
                value={replace[t.id] ?? ''}
                placeholder="Optional new Apprise URL"
                onChange={(e) => setReplace({ ...replace, [t.id]: e.target.value })}
              />
            </div>
            <Button
              size="sm"
              disabled={!replace[t.id]}
              onClick={() => {
                update(t.id, { url: replace[t.id] })
                setReplace({ ...replace, [t.id]: '' })
              }}
            >
              Save URL
            </Button>
          </div>
        </div>
      ))}

      <div className="space-y-3 rounded-md border border-dashed p-3">
        <h4 className="text-sm font-medium">Add target</h4>
        <div className="space-y-1">
          <Label htmlFor="new-target-name">Name</Label>
          <Input id="new-target-name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="new-target-url">Apprise URL</Label>
          <Input
            id="new-target-url"
            value={url}
            placeholder="discord://webhook_id/webhook_token"
            onChange={(e) => setUrl(e.target.value)}
          />
          <a
            href="https://github.com/caronc/apprise/wiki"
            target="_blank"
            rel="noreferrer"
            className="text-xs text-primary underline"
          >
            Apprise URL formats
          </a>
        </div>
        <TriggerBoxes idPrefix="new" all={triggers} value={newTriggers} onChange={setNewTriggers} />
        <div className="flex gap-2">
          <Button size="sm" variant="outline" disabled={!url} onClick={() => test.mutate({ url })}>
            Send test
          </Button>
          <Button size="sm" disabled={!name || !url || save.isPending} onClick={add}>
            Add target
          </Button>
        </div>
      </div>
    </div>
  )
}
