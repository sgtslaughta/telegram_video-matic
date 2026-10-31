import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Pause, Play, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads'
import { formatBytes } from '@/lib/format'
import { withToast } from '@/lib/toast'
import { post } from './data'
import { Bar, Dot, Empty, Row, RowSkeleton, Section } from './rows'
import { useRowNav } from '@/hooks/useRowNav'
import { QueuedRows } from './QueuedRows'

const GRID = 'grid-cols-[20px_minmax(0,1fr)_auto] md:grid-cols-[20px_minmax(0,1fr)_160px_80px_64px_72px_88px_84px]'

function eta(sec?: number | null) {
  if (!sec || sec <= 0) return '-'
  const m = Math.floor(sec / 60)
  return m ? `${m}m ${Math.floor(sec % 60)}s` : `${Math.floor(sec)}s`
}

export function QueueTab() {
  const qc = useQueryClient()
  const active = useActiveDownloads()
  const queued = useQueuedDownloads()
  const [sel, setSel] = useState<Set<number>>(new Set())
  const ref = useRowNav<HTMLDivElement>()
  const jobs = active.data ?? []
  const waiting = queued.data ?? []
  const refresh = () => qc.invalidateQueries({ queryKey: ['downloads'] })

  const act = (ids: number[], verb: 'pause' | 'resume' | 'cancel') => {
    const done = { pause: 'Paused', resume: 'Resumed', cancel: 'Canceled' }[verb]
    return withToast(async () => {
      await Promise.all(ids.map((id) => post(`/downloads/${id}/${verb}`)))
      setSel(new Set())
      refresh()
    }, { success: `${done} ${ids.length} download${ids.length === 1 ? '' : 's'}` })
  }
  const toggle = (id: number) => setSel((s) => { const n = new Set(s); if (!n.delete(id)) n.add(id); return n })
  const allSelected = jobs.length > 0 && sel.size === jobs.length

  const bulk = sel.size > 0 && (
    <div className="flex items-center gap-1">
      <span className="mr-1 text-[12px] text-muted-foreground">{sel.size} selected</span>
      <Button size="sm" variant="outline" className="h-7 px-2 text-[12px]" onClick={() => act([...sel], 'pause')}>Pause</Button>
      <Button size="sm" variant="outline" className="h-7 px-2 text-[12px]" onClick={() => act([...sel], 'cancel')}>Cancel</Button>
    </div>
  )

  if (active.isLoading) return <Section title="Queue"><RowSkeleton /></Section>
  if (!jobs.length && !waiting.length) {
    return <Section title="Queue"><Empty>Nothing downloading. New videos from your subscriptions queue here automatically.</Empty></Section>
  }

  return (
    <div ref={ref}>
      <Section title="Queue" aside={bulk || undefined}>
        <div role="table">
          <div role="row" className={`hidden h-9 items-center gap-x-3 border-b border-border px-4 text-[12px] text-muted-foreground md:grid ${GRID}`}>
            <Checkbox aria-label="Select all" className="rounded" checked={allSelected}
              onCheckedChange={() => setSel(allSelected ? new Set() : new Set(jobs.map((j) => j.id)))} />
            <span>Title</span><span>Progress</span><span className="text-right">Speed</span>
            <span className="text-right">ETA</span><span className="text-right">Size</span><span>Status</span><span />
          </div>
          {jobs.map((j) => {
            const paused = j.status === 'paused'
            return (
              <Row key={j.id} to={`/media/${j.media_id}`} selected={sel.has(j.id)} className={`min-h-10 py-1.5 ${GRID}`}>
                <Checkbox aria-label="Select download" className="rounded" checked={sel.has(j.id)} onCheckedChange={() => toggle(j.id)} />
                <div className="min-w-0">
                  <p className="truncate font-medium" title={j.file_name ?? undefined}>{j.file_name || `Download #${j.id}`}</p>
                  {j.error && <p className="truncate text-[12px] text-err">{j.error}</p>}
                  <div className="mt-1 md:hidden"><Bar value={j.progress ?? 0} /></div>
                </div>
                <div className="hidden md:block"><Bar value={j.progress ?? 0} /></div>
                <span className="hidden text-right tabular-nums text-muted-foreground md:block">{j.speed_bps ? `${formatBytes(j.speed_bps)}/s` : '-'}</span>
                <span className="hidden text-right tabular-nums text-muted-foreground md:block">{eta(j.eta_sec)}</span>
                <span className="hidden text-right tabular-nums text-muted-foreground md:block">{formatBytes(j.bytes_total)}</span>
                <span className="hidden items-center gap-1.5 md:flex"><Dot tone={paused ? 'muted' : 'warn'} />{paused ? 'Paused' : 'Downloading'}</span>
                <div className="flex justify-end gap-0.5">
                  <Button size="icon" variant="ghost" className="h-7 w-7" aria-label={paused ? 'Resume download' : 'Pause download'}
                    onClick={() => act([j.id], paused ? 'resume' : 'pause')}>
                    {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
                  </Button>
                  <Button size="icon" variant="ghost" className="h-7 w-7 hover:text-err" aria-label="Cancel download" onClick={() => act([j.id], 'cancel')}>
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </Row>
            )
          })}
          <QueuedRows items={waiting} grid={GRID} />
        </div>
      </Section>
    </div>
  )
}
