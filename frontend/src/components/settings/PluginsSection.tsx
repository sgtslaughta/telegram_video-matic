import { useState } from 'react'
import { AlertCircle, Clock, FolderSync, HardDriveDownload, RefreshCw, Wand2 } from 'lucide-react'
import { RugbyJobDialog } from '@/components/RugbyJobDialog'
import { RugbyMatchReview } from '@/components/RugbyMatchReview'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { usePlugins, useUpdatePlugin } from '@/hooks/usePlugins'
import { useRugbyRescan, useRugbyStatus } from '@/hooks/useRugby'
import { withToast } from '@/lib/toast'
import type * as T from '@/lib/types'
import { SettingsSection } from './SettingsSection'

type State = Record<string, { enabled: boolean; config: Record<string, unknown> }>

function RugbyTools({ enabled, rateLimited }: { enabled: boolean; rateLimited: boolean }) {
  const rescan = useRugbyRescan()
  const [job, setJob] = useState<T.RugbyJob | null>(null)
  const status = useRugbyStatus()
  const sync = (status.data?.status ?? {}) as Record<string, unknown>
  const done = Number(sync.sync_done ?? 0)
  const total = Number(sync.sync_total ?? 0)
  const current = (sync.sync_current as string | null) ?? null
  if (!enabled) return null
  const btn = 'h-8 text-[13px]'
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="outline" className={btn} disabled={rescan.isPending}
          onClick={() => withToast(() => rescan.mutateAsync(), { success: 'Scan started, fetching fixtures in the background', error: 'Scan failed' })}>
          <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${rescan.isPending ? 'animate-spin' : ''}`} />{rescan.isPending ? 'Scanning…' : 'Scan now'}
        </Button>
        <Button size="sm" variant="outline" className={btn} onClick={() => setJob('rematch')}
          title="Preview re-matching unmatched and auto-matched games, then apply"><Wand2 className="mr-1.5 h-3.5 w-3.5" />Re-match</Button>
        <Button size="sm" variant="outline" className={btn} onClick={() => setJob('reconcile')}
          title="Preview moving every rugby video into league/Season folders, then apply"><FolderSync className="mr-1.5 h-3.5 w-3.5" />Reorganize library</Button>
        <Button size="sm" variant="outline" className={btn} onClick={() => setJob('import')}
          title="Preview adopting video files already on disk, then import"><HardDriveDownload className="mr-1.5 h-3.5 w-3.5" />Import files</Button>
        {rateLimited && (
          <span className="inline-flex items-center gap-1 text-[12px] text-warn"><Clock className="h-3.5 w-3.5" />Rate limited, coverage may be incomplete</span>
        )}
      </div>
      {Boolean(sync.syncing) && (
        <div className="space-y-1">
          <div className="flex justify-between text-[12px] text-muted-foreground">
            <span>Syncing metadata{current ? `: ${current}` : ''}…</span>
            <span className="tabular-nums">{done}/{total || '—'}</span>
          </div>
          <ProgressBar progress={total ? (done / total) * 100 : 5} animated />
        </div>
      )}
      <RugbyMatchReview />
      {job && <RugbyJobDialog key={job} job={job} onClose={() => setJob(null)} />}
    </>
  )
}

export function PluginsSection() {
  const { data: plugins = [] } = usePlugins()
  const update = useUpdatePlugin()
  const server: State = Object.fromEntries(plugins.map((p) => [p.name, { enabled: p.enabled, config: p.config || {} }]))
  const [draft, setDraft] = useState<State>(server)
  const patch = (name: string, f: (s: State[string]) => State[string]) =>
    setDraft((d) => ({ ...d, [name]: f(d[name] ?? server[name]) }))
  const changed = plugins.filter((p) => JSON.stringify(draft[p.name]) !== JSON.stringify(server[p.name]))

  const save = () => withToast(
    () => Promise.all(changed.map((p) => update.mutateAsync({ name: p.name, config: { enabled: draft[p.name].enabled, ...draft[p.name].config } }))),
    { success: 'Plugin settings saved' },
  )

  return (
    <SettingsSection id="plugins" title="Plugins" description="Extra sources and matchers. Plugins run as application code, so only install ones you trust."
      dirty={changed.length > 0} saving={update.isPending} onSave={save}>
      {plugins.length === 0 && <p className="text-[13px] text-muted-foreground">No plugins installed.</p>}
      <div className="divide-y divide-border">
        {plugins.map((p) => {
          const st = draft[p.name] ?? server[p.name]
          const rateLimited = Boolean((p.status as Record<string, unknown> | undefined)?.rate_limited)
          return (
            <div key={p.id} className="space-y-4 py-4 first:pt-0 last:pb-0">
              {p.last_error && (
                <div className="flex gap-2 rounded-md bg-err/10 p-3 text-[13px]">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-err" /><p>{p.last_error}</p>
                </div>
              )}
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[13px] font-medium capitalize">{p.name}</p>
                  <p className="text-[12px] text-muted-foreground">v{p.version}</p>
                </div>
                <Switch aria-label={p.name} checked={st.enabled} onCheckedChange={(enabled) => patch(p.name, (s) => ({ ...s, enabled }))} />
              </div>
              {p.config_schema?.fields?.map((f) => (
                <div key={f.key} className="space-y-1.5">
                  <Label htmlFor={`${p.name}-${f.key}`} className="text-[13px] font-medium">{f.label}</Label>
                  {f.type === 'boolean' ? (
                    <div><Switch id={`${p.name}-${f.key}`} checked={(st.config[f.key] as boolean) ?? false}
                      onCheckedChange={(v) => patch(p.name, (s) => ({ ...s, config: { ...s.config, [f.key]: v } }))} /></div>
                  ) : (
                    <Input id={`${p.name}-${f.key}`} className="h-9 max-w-xs text-[13px]" type={f.type === 'number' ? 'number' : 'text'}
                      value={(st.config[f.key] as string) ?? ''}
                      onChange={(e) => patch(p.name, (s) => ({ ...s, config: { ...s.config, [f.key]: f.type === 'number' ? (e.target.value ? Number(e.target.value) : null) : e.target.value } }))} />
                  )}
                  {f.help && <p className="text-[12px] text-muted-foreground">{f.help}</p>}
                </div>
              ))}
              {p.name === 'rugby' && <RugbyTools enabled={st.enabled} rateLimited={rateLimited} />}
            </div>
          )
        })}
      </div>
      <p className="border-t border-border pt-4 text-[12px] text-muted-foreground">
        To install one, drop a <code className="rounded bg-muted px-1 font-mono">*_plugin.py</code> file into the{' '}
        <code className="rounded bg-muted px-1 font-mono">plugins/</code> directory and restart the container.
      </p>
    </SettingsSection>
  )
}
