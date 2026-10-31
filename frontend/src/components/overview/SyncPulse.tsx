import { Link } from 'react-router-dom'
import { Sparkline } from '@/components/shared/Sparkline'
import { absTime, relTime } from '@/lib/format'
import type { OverviewSub } from '@/hooks/useOverview'
import { outageSpans, type Span } from './spans'

function summary(s: OverviewSub, spans: Span[]): string {
  const found = s.pulse.reduce((n, c) => n + c.queued, 0)
  const offline = spans.filter((x) => x.kind === 'down').reduce((n, x) => n + x.to - x.from + 1, 0)
  const bits = [`${found} new video${found === 1 ? '' : 's'}`]
  if (offline) bits.push(`offline ${offline}h`)
  return bits.join(', ')
}

function Row({ s }: { s: OverviewSub }) {
  const spans = outageSpans(s.pulse)
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-6 gap-y-2 py-3 md:grid-cols-[minmax(0,200px)_1fr_auto]">
      <div className="min-w-0">
        <Link to={`/subscriptions/${s.id}`} className="block truncate text-[13px] font-medium hover:underline">{s.name}</Link>
        <p className="truncate text-[12px] text-muted-foreground">
          {s.live ? 'Live' : s.enabled ? summary(s, spans) : 'Paused'}
        </p>
      </div>
      <div role="img" aria-label={`${s.name}: ${summary(s, spans)}`} className="order-last col-span-2 min-w-0 overflow-hidden md:order-none md:col-span-1">
        <Sparkline data={s.pulse} dataKey="queued" label="New videos"
          bands={spans.map((x) => ({ from: x.from, to: x.to, tone: x.kind === 'down' ? 'err' : 'warn' }))} />
      </div>
      <span className="whitespace-nowrap text-right text-[12px] text-muted-foreground" title={absTime(s.last_checked_at)}>
        {s.enabled ? `Synced ${relTime(s.last_checked_at)}` : ''}
      </span>
    </div>
  )
}

export function SyncPulse({ subs }: { subs: OverviewSub[] }) {
  return <div className="divide-y divide-border">{subs.map((s) => <Row key={s.id} s={s} />)}</div>
}

export function PulseLegend() {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-muted-foreground">
      <li className="flex items-center gap-1.5"><span className="h-px w-4 bg-foreground" />New videos per hour</li>
      <li className="flex items-center gap-1.5"><span className="h-2.5 w-3 rounded-sm bg-err/20" />Telegram offline</li>
      <li className="flex items-center gap-1.5"><span className="h-2.5 w-3 rounded-sm bg-warn/20" />Failed polls</li>
    </ul>
  )
}
