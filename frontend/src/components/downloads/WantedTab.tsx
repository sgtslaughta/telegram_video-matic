import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { absTime, formatBytes, relTime } from '@/lib/format'
import { withToast } from '@/lib/toast'
import { cn } from '@/lib/utils'
import { dq, post, useFailed, useWanted, type WantedGame } from './data'
import { SearchDialog } from './SearchDialog'
import { Dot, Empty, Row, RowSkeleton, Section } from './rows'
import { useRowNav } from '@/hooks/useRowNav'

const STATE = { missing: ['Missing', 'warn'], searching: ['Searching', 'warn'], not_found: ['Not found', 'muted'] } as const

function GameRow({ g, onSearch, onDismiss }: { g: WantedGame; onSearch: () => void; onDismiss: () => void }) {
  const [label, tone] = STATE[g.state] ?? STATE.missing
  return (
    <Row className="min-h-11 grid-cols-[minmax(0,1fr)_auto] py-1.5 md:grid-cols-[minmax(0,1fr)_minmax(0,200px)_110px_110px_150px]">
      <div className="min-w-0">
        <p className="truncate font-medium">{g.home} vs {g.away}</p>
        <p className="truncate text-[12px] text-muted-foreground md:hidden">{g.league}{g.round ? `, round ${g.round}` : ''}, {relTime(g.date)}</p>
      </div>
      <p className="hidden truncate text-muted-foreground md:block">{g.league}{g.round ? `, round ${g.round}` : ''}</p>
      <span className="hidden text-muted-foreground md:block" title={absTime(g.date)}>{relTime(g.date)}</span>
      <span className={cn('hidden items-center gap-1.5 md:flex', g.state === 'not_found' && 'text-muted-foreground')}><Dot tone={tone} />{label}</span>
      <div className="flex justify-end gap-1">
        <Button size="sm" variant="outline" className="h-7 px-2 text-[12px]" onClick={onSearch}>Search</Button>
        <Button size="sm" variant="ghost" className="h-7 px-2 text-[12px]" onClick={onDismiss}>Dismiss</Button>
      </div>
    </Row>
  )
}

export function WantedTab() {
  const qc = useQueryClient()
  const wanted = useWanted()
  const failed = useFailed()
  const [target, setTarget] = useState<WantedGame | null>(null)
  const [sel, setSel] = useState<Set<number>>(new Set())
  const ref = useRowNav<HTMLDivElement>()
  const games = wanted.data
  const fails = failed.data ?? []

  const dismiss = (g: WantedGame) => withToast(async () => {
    await post(`/plugins/rugby/wanted/${g.fixture_id}/dismiss?subscription_id=${g.subscription_id}`)
    qc.invalidateQueries({ queryKey: dq.wanted })
  }, { success: `Dismissed ${g.home} vs ${g.away}` })

  const retry = (ids: number[]) => withToast(async () => {
    await Promise.all(ids.map((id) => post(`/media/${id}/requeue`)))
    setSel(new Set())
    qc.invalidateQueries({ queryKey: ['downloads'] })
  }, { success: `Retried ${ids.length} download${ids.length === 1 ? '' : 's'}` })

  const toggle = (id: number) => setSel((s) => { const n = new Set(s); if (!n.delete(id)) n.add(id); return n })
  const ids = sel.size ? [...sel] : fails.map((f) => f.media_id)

  return (
    <div ref={ref}>
      {games !== null && (
        <Section title="Missing games" aside={games && <span className="text-[12px] text-muted-foreground">{games.length}</span>}>
          {wanted.isLoading ? <RowSkeleton />
            : !games?.length ? <Empty>No missing games. Played fixtures without a video show up here.</Empty>
            : games.map((g) => <GameRow key={g.fixture_id} g={g} onSearch={() => setTarget(g)} onDismiss={() => dismiss(g)} />)}
        </Section>
      )}
      <Section title="Failed downloads" aside={fails.length > 0 && (
        <Button size="sm" variant="outline" className="h-7 px-2 text-[12px]" onClick={() => retry(ids)}>
          {sel.size ? `Retry ${sel.size} selected` : 'Retry all'}
        </Button>
      )}>
        {failed.isLoading ? <RowSkeleton />
          : !fails.length ? <Empty>No failed downloads.</Empty>
          : fails.map((f) => (
            <Row key={f.media_id} to={`/media/${f.media_id}`} selected={sel.has(f.media_id)}
              className="min-h-11 grid-cols-[20px_minmax(0,1fr)_auto] py-1.5 md:grid-cols-[20px_minmax(0,1fr)_minmax(0,260px)_80px_110px_90px]">
              <Checkbox aria-label="Select failed download" className="rounded" checked={sel.has(f.media_id)} onCheckedChange={() => toggle(f.media_id)} />
              <div className="min-w-0">
                <Link to={`/media/${f.media_id}`} className="block truncate font-medium hover:underline">{f.file_name || f.caption || `Media #${f.media_id}`}</Link>
                <p className="truncate text-[12px] text-err md:hidden">{f.error}</p>
              </div>
              <p className="hidden truncate text-[12px] text-err md:block" title={f.error ?? undefined}>{f.error}</p>
              <span className="hidden text-right tabular-nums text-muted-foreground md:block">{formatBytes(f.size_bytes)}</span>
              <span className="hidden text-muted-foreground md:block" title={absTime(f.last_attempt_at)}>{relTime(f.last_attempt_at)}</span>
              <div className="flex justify-end">
                <Button size="sm" variant="ghost" className="h-7 px-2 text-[12px]" onClick={() => retry([f.media_id])}>Retry download</Button>
              </div>
            </Row>
          ))}
      </Section>
      <SearchDialog game={target} onClose={() => setTarget(null)} />
    </div>
  )
}
