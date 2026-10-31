import { useInfiniteQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Ban, CheckCircle2, CircleDot, Link2, Trash2, XCircle, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { fetchAPI } from '@/lib/api'
import { absTime, relTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { HistoryItem } from './data'
import { dq } from './data'
import { Empty, Row, RowSkeleton, Section } from './rows'
import { useRowNav } from '@/hooks/useRowNav'

const PAGE = 50
const KINDS: [string, string][] = [['', 'All'], ['downloaded', 'Downloaded'], ['failed', 'Failed'], ['skipped', 'Skipped'], ['deleted', 'Deleted'], ['matched', 'Matched']]
const ICON: Record<string, [LucideIcon, string]> = {
  downloaded: [CheckCircle2, 'text-ok'], failed: [XCircle, 'text-err'], skipped: [Ban, 'text-muted-foreground'],
  deleted: [Trash2, 'text-muted-foreground'], matched: [Link2, 'text-brand'], other: [CircleDot, 'text-muted-foreground'],
}

export function HistoryTab({ kind, setKind }: { kind: string; setKind: (k: string) => void }) {
  const q = useInfiniteQuery({
    queryKey: [...dq.history, kind],
    initialPageParam: 0,
    queryFn: ({ pageParam }) => fetchAPI<HistoryItem[]>('/history', { params: { limit: PAGE, offset: pageParam, kind } }),
    getNextPageParam: (last, all) => (last.length < PAGE ? undefined : all.length * PAGE),
  })
  const ref = useRowNav<HTMLDivElement>()
  const items = q.data?.pages.flat() ?? []

  const chips = (
    <div role="radiogroup" aria-label="Filter by type" className="flex flex-wrap gap-1 text-[12px]">
      {KINDS.map(([k, l]) => (
        <button key={k} role="radio" aria-checked={kind === k} onClick={() => setKind(k)}
          className={cn('rounded-md border px-2 py-0.5 transition-colors', kind === k ? 'border-brand/30 bg-brand/10 font-medium text-brand' : 'border-border text-muted-foreground hover:text-foreground')}>
          {l}
        </button>
      ))}
    </div>
  )

  return (
    <div ref={ref}>
      <Section title="History" aside={<div className="hidden sm:block">{chips}</div>}>
        <div className="border-b border-border px-4 py-2 sm:hidden">{chips}</div>
        {q.isLoading ? <RowSkeleton n={6} />
          : !items.length ? <Empty>No history yet. Downloads, failures and skipped videos are recorded here.</Empty>
          : items.map((h, i) => {
            const [Icon, tone] = ICON[h.kind] ?? ICON.other
            return (
              <Row key={`${h.at}-${i}`} to={h.media_id ? `/media/${h.media_id}` : undefined} className="min-h-10 grid-cols-[16px_minmax(0,1fr)_auto] py-1.5">
                <Icon className={cn('h-4 w-4', tone)} strokeWidth={1.75} aria-label={h.kind} />
                <div className="min-w-0">
                  {h.media_id
                    ? <Link to={`/media/${h.media_id}`} className="block truncate font-medium hover:underline">{h.file_name || h.message}</Link>
                    : <p className="truncate font-medium">{h.file_name || h.message}</p>}
                  {h.file_name && <p className="truncate text-[12px] text-muted-foreground">{h.message}</p>}
                </div>
                <span className="whitespace-nowrap text-[12px] text-muted-foreground" title={absTime(h.at)}>{relTime(h.at)}</span>
              </Row>
            )
          })}
        {q.hasNextPage && (
          <div className="border-t border-border p-2 text-center">
            <Button variant="ghost" size="sm" disabled={q.isFetchingNextPage} onClick={() => q.fetchNextPage()}>Load more</Button>
          </div>
        )}
      </Section>
    </div>
  )
}
