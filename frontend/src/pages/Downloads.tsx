import { useActiveDownloads } from '@/hooks/useDownloads'
import { useWebSocket } from '@/hooks/useWebSocket'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function fmtBytes(n?: number | null): string {
  if (!n || n <= 0) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), u.length - 1)
  return `${(n / 1024 ** i).toFixed(1)} ${u[i]}`
}

function fmtEta(sec?: number | null): string {
  if (!sec || sec <= 0) return '—'
  const m = Math.floor(sec / 60)
  return m > 0 ? `${m}m ${Math.floor(sec % 60)}s` : `${Math.floor(sec)}s`
}

export default function Downloads() {
  // Mounting the socket here keeps progress live even if no other page has it open.
  useWebSocket()
  const { data, isLoading } = useActiveDownloads()
  const jobs = data ?? []

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Downloads</h1>
        <p className="mt-1 text-sm text-muted-foreground">Live progress of active downloads</p>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-muted-foreground">Loading…</div>
      ) : jobs.length === 0 ? (
        <EmptyState title="No active downloads" message="Queued and in-progress downloads will appear here in real time." />
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Card key={job.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Download #{job.id}</CardTitle>
                <StatusBadge status={job.status} />
              </CardHeader>
              <CardContent className="space-y-2">
                <ProgressBar progress={job.progress} animated showLabel />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>
                    {job.bytes_total
                      ? `${fmtBytes(job.bytes_done)} / ${fmtBytes(job.bytes_total)}`
                      : fmtBytes(job.bytes_done)}
                  </span>
                  <span>{job.speed_bps ? `${fmtBytes(job.speed_bps)}/s` : '—'}</span>
                  <span>ETA {fmtEta(job.eta_sec)}</span>
                </div>
                {job.error && <p className="text-xs text-destructive">{job.error}</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
