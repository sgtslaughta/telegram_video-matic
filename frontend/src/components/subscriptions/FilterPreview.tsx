import { Loader2 } from 'lucide-react'
import { absTime, formatBytes } from '@/lib/format'
import type { PreviewItem } from '@/hooks/useSubscriptionTools'

/** Live result of the current filter against recent posts. */
export function FilterPreview({ items, loading, idle }: { items?: PreviewItem[]; loading: boolean; idle: boolean }) {
  const down = items?.filter((i) => i.would === 'download').length ?? 0
  const skipped = (items?.length ?? 0) - down
  return (
    <div className="rounded-md border border-border bg-muted/40" aria-label="Filter preview">
      <div className="flex h-9 items-center justify-between border-b border-border px-3">
        <h3 className="text-[12px] font-semibold">Filter preview</h3>
        {loading && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" aria-label="Loading" />}
      </div>
      {idle ? (
        <p className="px-3 py-3 text-[12px] text-muted-foreground">Pick a channel to preview what the filter would catch.</p>
      ) : !items ? (
        <p className="px-3 py-3 text-[12px] text-muted-foreground">{loading ? 'Checking recent posts…' : ''}</p>
      ) : items.length === 0 ? (
        <p className="px-3 py-3 text-[12px] text-muted-foreground">No recent posts with media to check.</p>
      ) : (
        <>
          <p className="px-3 pt-2 text-[12px] text-muted-foreground" data-testid="preview-counts">
            <span className="font-medium text-foreground">{down} would download</span>, {skipped} skipped
          </p>
          <ul className="max-h-64 divide-y divide-border overflow-y-auto px-3 py-1">
            {items.map((i) => (
              <li key={i.tg_msg_id} className="flex items-center gap-2 py-1.5 text-[12px]">
                <span className={`h-2 w-2 shrink-0 rounded-full ${i.would === 'download' ? 'bg-ok' : 'bg-muted-foreground/40'}`} />
                <span className="min-w-0 flex-1 truncate" title={i.caption ?? undefined}>{i.file_name || i.caption || `Post ${i.tg_msg_id}`}</span>
                <span className="shrink-0 text-muted-foreground" title={absTime(i.date_posted)}>
                  {i.would === 'skip' ? i.reason : i.size_bytes ? formatBytes(i.size_bytes) : ''}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
