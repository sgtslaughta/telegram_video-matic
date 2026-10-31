import { Link } from 'react-router-dom'
import { ChevronRight, Film } from 'lucide-react'
import { Page, PageHeader } from '@/components/shared/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { SyncPulse, PulseLegend } from '@/components/overview/SyncPulse'
import { StatTile } from '@/components/shared/Sparkline'
import { useOverview, type Overview as O, type Arrival } from '@/hooks/useOverview'
import { usePersistedState } from '@/hooks/usePersistedState'
import { absTime, formatBytes, formatDuration, relTime } from '@/lib/format'
import { cn } from '@/lib/utils'

function healthLine(o: O): string {
  if (o.telegram.status === 'disconnected') return 'Telegram is disconnected. Sync resumes automatically once it reconnects.'
  if (o.telegram.status === 'unconfigured') return 'Connect a Telegram account to start syncing.'
  const n = o.subscriptions.filter((s) => s.enabled).length
  return `${n} active subscription${n === 1 ? '' : 's'}, last synced ${relTime(o.telegram.last_ok_poll_at)}.`
}

function Section({ title, aside, children, className }: { title: string; aside?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={cn('min-w-0 rounded-lg border border-border bg-card', className)}>
      <div className="flex h-11 items-center justify-between border-b border-border px-4">
        <h2 className="text-[13px] font-semibold">{title}</h2>
        {aside}
      </div>
      <div className="px-4">{children}</div>
    </section>
  )
}

function RangeToggle({ value, onChange }: { value: number; onChange: (h: number) => void }) {
  return (
    <div role="radiogroup" aria-label="Range" className="flex rounded-md border border-border p-0.5 text-[12px]">
      {[[24, '24h'], [168, '7d']].map(([h, l]) => (
        <button key={h} role="radio" aria-checked={value === h} onClick={() => onChange(h as number)}
          className={cn('rounded px-2 py-0.5 transition-colors', value === h ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:text-foreground')}>
          {l}
        </button>
      ))}
    </div>
  )
}

function ArrivalRow({ a }: { a: Arrival }) {
  return (
    <li>
      <Link to={`/media/${a.id}`} className="-mx-2 flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-accent/60">
        <div className="flex h-9 w-16 shrink-0 items-center justify-center overflow-hidden rounded bg-muted">
          {a.has_thumb
            ? <img src={`/api/media/${a.id}/thumb`} alt="" loading="lazy" className="h-full w-full object-cover" />
            : <Film className="h-4 w-4 text-muted-foreground/60" strokeWidth={1.5} />}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-medium">{a.title}</p>
          <p className="truncate text-[12px] text-muted-foreground">
            {[a.subtitle, formatDuration(a.duration_sec), a.size_bytes ? formatBytes(a.size_bytes) : null].filter(Boolean).join(', ')}
          </p>
        </div>
        <span className="shrink-0 text-[12px] text-muted-foreground" title={absTime(a.at)}>{relTime(a.at)}</span>
      </Link>
    </li>
  )
}

function AttentionRow({ to, count, label, tone }: { to: string; count: number; label: string; tone: 'err' | 'warn' }) {
  return (
    <li>
      <Link to={to} className="-mx-2 flex items-center gap-3 rounded-md px-2 py-2 text-[13px] transition-colors hover:bg-accent/60">
        <span className={cn('h-2 w-2 rounded-full', tone === 'err' ? 'bg-err' : 'bg-warn')} />
        <span className="flex-1">{label}</span>
        <span className="tabular-nums text-muted-foreground">{count}</span>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </Link>
    </li>
  )
}

export default function Overview() {
  const [hours, setHours] = usePersistedState<number>('overview.hours', 24)
  const { data, isLoading, error } = useOverview(hours)

  if (error) {
    return (
      <Page>
        <PageHeader title="Overview" />
        <p className="text-[13px] text-muted-foreground">The overview couldn’t load ({String((error as Error).message)}). It retries every 30 seconds.</p>
      </Page>
    )
  }

  const att = data?.attention
  const attention = att ? [
    att.failed > 0 && <AttentionRow key="f" to="/downloads?tab=wanted" count={att.failed} label="Downloads failed" tone="err" />,
    att.cleanup_paused && <AttentionRow key="c" to="/storage" count={att.cleanup_paused.count} label={`Cleanup waiting for approval (${att.cleanup_paused.gb} GB)`} tone="warn" />,
    att.needs_review > 0 && <AttentionRow key="r" to="/downloads?tab=review" count={att.needs_review} label="Videos need a match review" tone="warn" />,
    att.wanted > 0 && <AttentionRow key="w" to="/downloads?tab=wanted" count={att.wanted} label="Played games with no video yet" tone="warn" />,
  ].filter(Boolean) : []

  return (
    <Page>
      <PageHeader title="Overview" description={data ? healthLine(data) : <Skeleton className="h-4 w-64" />} />

      <Section title="Sync" aside={<RangeToggle value={hours} onChange={setHours} />}>
        {isLoading || !data ? (
          <div className="space-y-3 py-3">{[0, 1].map((i) => <Skeleton key={i} className="h-5 w-full" />)}</div>
        ) : data.subscriptions.length ? (
          <>
            <SyncPulse subs={data.subscriptions} />
            <div className="flex items-center justify-between gap-4 border-t border-border py-2.5">
              <PulseLegend />
              <span className="whitespace-nowrap text-[12px] text-muted-foreground">{hours === 24 ? 'Last 24 hours' : 'Last 7 days'}</span>
            </div>
          </>
        ) : (
          <p className="py-6 text-[13px] text-muted-foreground">
            No subscriptions yet. <Link to="/subscriptions" className="font-medium text-brand hover:underline">Add one</Link> to start syncing a channel.
          </p>
        )}
      </Section>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Section title="Recent arrivals" aside={<Link to="/downloads?tab=history" className="text-[12px] font-medium text-brand hover:underline">History</Link>}>
          {isLoading || !data ? (
            <div className="space-y-3 py-3">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-9 w-full" />)}</div>
          ) : data.recent.length ? (
            <ul className="py-1.5">{data.recent.map((a) => <ArrivalRow key={a.id} a={a} />)}</ul>
          ) : (
            <p className="py-6 text-[13px] text-muted-foreground">Nothing downloaded yet. New videos appear here as they finish.</p>
          )}
        </Section>

        <div className="min-w-0 space-y-4">
          <Section title="Needs attention">
            {attention.length ? <ul className="py-1.5">{attention}</ul> : (
              <p className="py-4 text-[13px] text-muted-foreground">{data ? 'Nothing needs you right now.' : ''}</p>
            )}
          </Section>
          {data && (
            <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border text-[13px]">
              <StatTile label="Downloaded, 24h" value={data.last_24h.downloaded} data={data.last_24h.series} dataKey="count" />
              <StatTile label="Added, 24h" value={formatBytes(data.last_24h.bytes)} data={data.last_24h.series} dataKey="bytes" format={formatBytes} />
            </dl>
          )}
        </div>
      </div>
    </Page>
  )
}
