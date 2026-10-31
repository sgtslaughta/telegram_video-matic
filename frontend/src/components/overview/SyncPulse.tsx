import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { absTime, relTime } from '@/lib/format'
import type { OverviewSub, PulseCell } from '@/hooks/useOverview'

function cellState(c: PulseCell): 'error' | 'down' | 'ok' | 'none' {
  if (c.error) return 'error'
  if (c.down) return 'down'
  if (c.ok) return 'ok'
  return 'none'
}

const COLOR = { error: 'bg-err', down: 'bg-err/45', ok: 'bg-ok', none: 'bg-idle' } as const
const LABEL = { error: 'errors', down: 'Telegram offline', ok: 'synced', none: 'no polls' } as const

function describe(c: PulseCell) {
  const s = cellState(c)
  const when = new Date(c.t).toLocaleString(undefined, { weekday: 'short', hour: 'numeric' })
  const parts = [`${when}: ${LABEL[s]}`]
  if (c.queued) parts.push(`${c.queued} new`)
  if (c.error) parts.push(`${c.error} failed polls`)
  return parts.join(', ')
}

export function SyncPulse({ subs }: { subs: OverviewSub[] }) {
  return (
    <div className="divide-y divide-border">
      {subs.map((s) => (
        <div key={s.id} className="grid grid-cols-[minmax(0,180px)_1fr_auto] items-center gap-4 py-2.5">
          <Link to={`/subscriptions/${s.id}`} className="truncate text-[13px] font-medium hover:underline">
            {s.name}
          </Link>
          {s.live ? (
            <p className="text-[12px] text-muted-foreground">Live: new posts sync as they arrive</p>
          ) : (
            <ol className="flex h-5 gap-px" aria-label={`${s.name} sync history`}>
              {s.pulse.map((c) => {
                const st = cellState(c)
                return (
                  <li key={c.t} title={describe(c)} aria-label={describe(c)}
                    className={cn('relative flex-1 rounded-[2px]', COLOR[st], !s.enabled && 'opacity-40')}>
                    {c.queued > 0 && <span className="absolute inset-x-0 top-0 mx-auto h-1 w-1 rounded-full bg-background" />}
                  </li>
                )
              })}
            </ol>
          )}
          <span className="w-24 text-right text-[12px] text-muted-foreground" title={absTime(s.last_checked_at)}>
            {s.enabled ? relTime(s.last_checked_at) : 'Paused'}
          </span>
        </div>
      ))}
    </div>
  )
}

export function PulseLegend() {
  const items: [string, string][] = [['bg-ok', 'Synced'], ['bg-err', 'Errors'], ['bg-err/45', 'Telegram offline'], ['bg-idle', 'No polls']]
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-muted-foreground">
      {items.map(([c, l]) => (
        <li key={l} className="flex items-center gap-1.5"><span className={cn('h-2.5 w-2.5 rounded-[2px]', c)} />{l}</li>
      ))}
      <li className="flex items-center gap-1.5">
        <span className="relative h-2.5 w-2.5 rounded-[2px] bg-ok"><span className="absolute inset-x-0 top-0 mx-auto h-1 w-1 rounded-full bg-background" /></span>
        New videos found
      </li>
    </ul>
  )
}
