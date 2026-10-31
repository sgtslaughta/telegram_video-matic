import { Link } from 'react-router-dom'
import { absTime, relTime } from '@/lib/format'
import type { FeedEvent } from './useEventsFeed'

const DOT: Record<string, string> = {
  info: 'bg-muted-foreground/50', success: 'bg-ok', warning: 'bg-warn', error: 'bg-err',
}

export function EventRow({ e, index, active, onHover }: { e: FeedEvent; index: number; active: boolean; onHover: (i: number) => void }) {
  const when = e.updated_at ?? e.created_at
  const n = e.count ?? 1
  const link = e.media_id ? `/media/${e.media_id}` : e.subscription_id ? `/subscriptions/${e.subscription_id}` : null
  return (
    <li
      data-nav={index}
      onMouseEnter={() => onHover(index)}
      className={`flex min-h-10 items-center gap-3 px-4 py-2 transition-colors ${active ? 'bg-accent/60' : ''}`}
    >
      <span className={`h-2 w-2 shrink-0 rounded-full ${DOT[e.level] ?? DOT.info}`} role="img" aria-label={e.level} />
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-2 gap-y-0.5">
        {link ? (
          <Link to={link} className="min-w-0 break-words text-[13px] hover:underline">{e.message}</Link>
        ) : (
          <span className="min-w-0 break-words text-[13px]">{e.message}</span>
        )}
        {n > 1 && (
          <span
            className="rounded-full bg-muted px-1.5 text-[11px] font-medium text-muted-foreground"
            title={`Repeated ${n} times, last ${relTime(when)}`}
          >
            ×{n}
          </span>
        )}
      </div>
      <span className="hidden rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground sm:inline">{e.kind}</span>
      <span className="w-20 shrink-0 text-right text-[12px] text-muted-foreground" title={absTime(when)}>{relTime(when)}</span>
    </li>
  )
}
