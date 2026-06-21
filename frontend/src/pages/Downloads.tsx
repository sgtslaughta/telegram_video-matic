import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Trash2, Pause, Play, X } from 'lucide-react'
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads'
import { useWebSocket } from '@/hooks/useWebSocket'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/shared'
import * as api from '@/lib/api'

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
  const qc = useQueryClient()
  const { data, isLoading } = useActiveDownloads()
  const jobs = data ?? []
  const { data: queuedData } = useQueuedDownloads()
  const queued = queuedData ?? []
  const [confirmOpen, setConfirmOpen] = useState(false)

  const clearAll = async () => {
    setConfirmOpen(false)
    try {
      await api.media.clear()
      qc.invalidateQueries()
      toast.success('Cleared media & download jobs')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Clear failed')
    }
  }

  const act = async (fn: () => Promise<unknown>, label: string) => {
    try {
      await fn()
      qc.invalidateQueries({ queryKey: ['downloads', 'active'] })
      toast.success(label)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : `${label} failed`)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Downloads</h1>
          <p className="mt-1 text-sm text-muted-foreground">Live progress of active downloads</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setConfirmOpen(true)}>
          <Trash2 className="mr-2 h-4 w-4" /> Clear data
        </Button>
      </div>

      <ConfirmDialog
        isOpen={confirmOpen}
        title="Clear all media & downloads?"
        description="Removes every media item and download job. Your account, subscriptions, and channels are kept. This cannot be undone."
        confirmText="Clear data"
        onConfirm={clearAll}
        onCancel={() => setConfirmOpen(false)}
      />

      {isLoading ? (
        <div className="py-12 text-center text-muted-foreground">Loading…</div>
      ) : jobs.length === 0 && queued.length === 0 ? (
        <EmptyState title="No active downloads" message="Queued and in-progress downloads will appear here in real time." />
      ) : (
       <>
        {jobs.length > 0 && (
        <div className="divide-y divide-border rounded-lg border">
          {jobs.map((job) => (
            <div key={job.id} className="flex items-center gap-4 px-4 py-2.5">
              <div className="w-28 shrink-0">
                <StatusBadge status={job.status} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="mb-1 truncate text-sm" title={job.file_name ?? undefined}>
                  {job.file_name || `Download #${job.id}`}
                </p>
                <ProgressBar progress={(job.progress ?? 0) * 100} animated />
                {job.error && <p className="mt-1 text-xs text-destructive">{job.error}</p>}
              </div>
              <div className="flex w-44 shrink-0 justify-end gap-3 text-xs tabular-nums text-muted-foreground">
                <span className="w-12 text-right font-medium text-foreground">
                  {Math.round((job.progress ?? 0) * 100)}%
                </span>
                <span>{job.speed_bps ? `${fmtBytes(job.speed_bps)}/s` : '—'}</span>
                <span>{fmtEta(job.eta_sec)}</span>
              </div>
              <div className="flex shrink-0 gap-1">
                {job.status === 'paused' ? (
                  <Button size="icon" variant="ghost" aria-label="Resume"
                    onClick={() => act(() => api.downloads.resume(job.id), 'Resumed')}>
                    <Play className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button size="icon" variant="ghost" aria-label="Pause"
                    onClick={() => act(() => api.downloads.pause(job.id), 'Paused')}>
                    <Pause className="h-4 w-4" />
                  </Button>
                )}
                <Button size="icon" variant="ghost" aria-label="Cancel"
                  className="text-destructive hover:text-destructive"
                  onClick={() => act(() => api.downloads.cancel(job.id), 'Canceled')}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
        )}

        {queued.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">
              Queued — waiting for a slot ({queued.length})
            </p>
            <div className="divide-y divide-border rounded-lg border">
              {queued.map((q) => (
                <div key={q.media_id} className="flex items-center gap-4 px-4 py-2">
                  <div className="w-28 shrink-0"><StatusBadge status="pending" /></div>
                  <p className="min-w-0 flex-1 truncate text-sm" title={q.file_name ?? undefined}>
                    {q.file_name || `Media #${q.media_id}`}
                  </p>
                  <span className="shrink-0 text-xs tabular-nums text-muted-foreground">{fmtBytes(q.size_bytes)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
       </>
      )}
    </div>
  )
}
