import { formatBytes } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Storage } from '@/hooks/useStorage'

export function DiskUsage({ s }: { s: Storage }) {
  const pct = Math.min(100, Math.max(0, s.disk.pct))
  const tone = pct > 90 ? 'bg-err' : pct > 80 ? 'bg-warn' : 'bg-brand'
  return (
    <section className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-[13px]">
          <span className="text-[20px] font-semibold tracking-tight">{Math.round(pct)}%</span>{' '}
          <span className="text-muted-foreground">{formatBytes(s.disk.used)} of {formatBytes(s.disk.total)} used</span>
        </p>
        <code className="truncate font-mono text-[12px] text-muted-foreground" title={s.media_root}>{s.media_root}</code>
      </div>
      <div role="progressbar" aria-label="Disk usage" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}
        className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
        <div className={cn('h-full rounded-full transition-colors', tone)} style={{ width: `${pct}%` }} />
      </div>
    </section>
  )
}
