import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { Page, PageHeader } from '@/components/shared/PageHeader'
import { EmptyState } from '@/components/shared/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { EventRow } from '@/components/activity/EventRow'
import { useEventsFeed } from '@/components/activity/useEventsFeed'
import { useListNav } from '@/hooks/useMediaTools'

const LEVELS = [
  { value: '', label: 'All' }, { value: 'info', label: 'Info' }, { value: 'success', label: 'Success' },
  { value: 'warning', label: 'Warnings' }, { value: 'error', label: 'Errors' },
]
const BASE_KINDS = ['subscription', 'download', 'job', 'sync', 'telegram', 'notify']

export default function Activity() {
  const [params, setParams] = useSearchParams()
  const level = params.get('level') ?? ''
  const kind = params.get('kind') ?? ''
  const q = params.get('q') ?? ''
  const set = (k: string, v: string) =>
    setParams((p) => { const n = new URLSearchParams(p); if (v) n.set(k, v); else n.delete(k); return n }, { replace: true })

  const feed = useEventsFeed({ level, kind })
  const all = useMemo(() => feed.data?.pages.flat() ?? [], [feed.data])
  const events = useMemo(() => {
    const s = q.toLowerCase()
    return s ? all.filter((e) => `${e.message} ${e.kind}`.toLowerCase().includes(s)) : all
  }, [all, q])
  const kinds = useMemo(() => [...new Set([...BASE_KINDS, ...all.map((e) => e.kind), ...(kind ? [kind] : [])])].sort(), [all, kind])

  const { active, setActive, searchRef } = useListNav(events.length, () => {})

  return (
    <Page>
      <PageHeader title="Activity" description="Everything the app has done, newest first." />
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div role="group" aria-label="Level" className="flex flex-wrap gap-1">
          {LEVELS.map((l) => (
            <button
              key={l.value}
              aria-pressed={level === l.value}
              onClick={() => set('level', l.value)}
              className={`h-8 rounded-md px-3 text-[13px] transition-colors ${level === l.value ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:bg-accent/60'}`}
            >
              {l.label}
            </button>
          ))}
        </div>
        <select
          aria-label="Kind"
          value={kind}
          onChange={(e) => set('kind', e.target.value)}
          className="h-8 rounded-md border border-input bg-background px-2 text-[13px] focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">All kinds</option>
          {kinds.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <div className="relative ml-auto w-full sm:w-64">
          <Search className="pointer-events-none absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input
            ref={searchRef}
            value={q}
            onChange={(e) => set('q', e.target.value)}
            placeholder="Search events (/)"
            aria-label="Search events"
            className="h-8 pl-8 text-[13px]"
          />
        </div>
      </div>

      <section className="rounded-lg border bg-card">
        {feed.isLoading ? (
          <div className="divide-y divide-border" aria-busy="true">
            {Array.from({ length: 10 }, (_, i) => (
              <div key={i} className="flex h-10 items-center gap-3 px-4">
                <Skeleton className="h-2 w-2 rounded-full" />
                <Skeleton className="h-3.5 flex-1" style={{ maxWidth: `${40 + ((i * 17) % 45)}%` }} />
                <Skeleton className="ml-auto h-3.5 w-16" />
              </div>
            ))}
          </div>
        ) : events.length === 0 ? (
          <EmptyState title="No events" message={q || level || kind ? 'Nothing matches these filters. Clear them to see everything.' : 'Events will appear here as the app syncs and downloads.'} />
        ) : (
          <ul className="divide-y divide-border">
            {events.map((e, i) => <EventRow key={e.id} e={e} index={i} active={i === active} onHover={setActive} />)}
          </ul>
        )}
      </section>

      {feed.hasNextPage && (
        <div className="flex justify-center pt-4">
          <Button variant="outline" onClick={() => feed.fetchNextPage()} disabled={feed.isFetchingNextPage}>
            {feed.isFetchingNextPage ? 'Loading…' : 'Load more'}
          </Button>
        </div>
      )}
    </Page>
  )
}
