import { Link } from 'react-router-dom'
import { Thumb } from '@/components/shared/Thumb'
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads'
import { formatBytes } from '@/lib/format'

function eta(sec?: number | null) {
  if (!sec || sec <= 0) return ''
  const m = Math.round(sec / 60)
  return m >= 60 ? `${Math.floor(m / 60)}h ${m % 60}m left` : `${m || 1}m left`
}

/** Live list of running downloads (WebSocket-updated) for the Overview. */
export function DownloadingNow() {
  const { data: active } = useActiveDownloads()
  const { data: queued } = useQueuedDownloads()
  const running = (active ?? []).filter((j) => j.status === 'running' || j.status === 'downloading')
  if (!running.length) return null
  const total = running.reduce((n, j) => n + (j.speed_bps ?? 0), 0)
  const waiting = queued?.length ?? 0
  return (
    <section className="mb-4 min-w-0 rounded-lg border border-border bg-card">
      <div className="flex h-11 items-center justify-between border-b border-border px-4">
        <h2 className="text-[13px] font-semibold">Downloading now</h2>
        <span className="text-[12px] tabular-nums text-muted-foreground">
          {formatBytes(total)}/s total{waiting ? `, ${waiting} waiting` : ''}
          <Link to="/downloads?tab=queue" className="ml-3 font-medium text-brand hover:underline">Queue</Link>
        </span>
      </div>
      <ul className="divide-y divide-border px-4">
        {running.map((j) => {
          const pct = Math.round((j.progress ?? 0) * 100)
          return (
            <li key={j.id}>
              <Link to={`/media/${j.media_id}`} className="-mx-2 flex items-center gap-3 rounded-md px-2 py-2.5 transition-colors hover:bg-accent/60">
                <Thumb id={j.media_id} className="h-9 w-16 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-medium">{j.file_name || `Media #${j.media_id}`}</p>
                  <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-muted" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
                    <div className="h-full rounded-full bg-brand transition-[width] duration-500" style={{ width: `${pct}%` }} />
                  </div>
                </div>
                <div className="w-28 shrink-0 text-right text-[12px] tabular-nums text-muted-foreground">
                  <div className="font-medium text-foreground">{pct}%</div>
                  <div>{j.speed_bps ? `${formatBytes(j.speed_bps)}/s` : ''} {eta(j.eta_sec)}</div>
                </div>
              </Link>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
