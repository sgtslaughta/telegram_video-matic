import { Skeleton } from '@/components/ui/skeleton'
import { absTime, relTime } from '@/lib/format'
import type { HistoryEntry } from '@/hooks/useMediaTools'

const DOT: Record<string, string> = { info: 'bg-muted-foreground/50', success: 'bg-ok', warning: 'bg-warn', error: 'bg-err' }

export function HistoryTimeline({ entries, loading }: { entries?: HistoryEntry[]; loading: boolean }) {
  if (loading) {
    return <div className="space-y-3 p-4" aria-busy="true">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-4 w-3/4" />)}</div>
  }
  if (!entries?.length) return <p className="p-4 text-[13px] text-muted-foreground">No history yet. Events for this video will show up here.</p>
  return (
    <ol className="p-4">
      {entries.map((h, i) => (
        <li key={`${h.at}-${i}`} className="relative flex gap-3 pb-4 last:pb-0">
          {i < entries.length - 1 && <span className="absolute left-[3px] top-3 h-full w-px bg-border" />}
          <span className={`relative mt-1.5 h-2 w-2 shrink-0 rounded-full ${DOT[h.level] ?? DOT.info}`} />
          <div className="min-w-0 flex-1">
            <p className="break-words text-[13px]">{h.message}</p>
            <p className="text-[12px] text-muted-foreground">
              <span>{h.kind}</span> · <span title={absTime(h.at)}>{relTime(h.at)}</span>
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}
