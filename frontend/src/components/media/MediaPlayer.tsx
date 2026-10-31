import { AlertTriangle, Ban, Download, Loader2, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { formatBytes } from '@/lib/format'
import type { MediaFull } from '@/hooks/useMediaTools'

interface Props {
  item: MediaFull
  progress?: { progress: number; bytes_done?: number; bytes_total?: number } | null
  busy: boolean
  onDownload: () => void
  onRetry: () => void
}

const frame = 'aspect-video w-full overflow-hidden rounded-lg border bg-black'

export function MediaPlayer({ item, progress, busy, onDownload, onRetry }: Props) {
  if (item.status === 'downloaded') {
    return (
      <div className={frame}>
        <video
          controls
          preload="metadata"
          src={`/api/media/${item.id}/stream`}
          poster={`/api/media/${item.id}/thumb`}
          className="h-full w-full"
        />
      </div>
    )
  }

  const failed = item.status === 'failed'
  const skipped = !!item.skip_reason && !failed
  const loading = item.status === 'downloading' || item.status === 'processing'
  const Icon = failed ? AlertTriangle : skipped ? Ban : loading ? Loader2 : Download
  const title = failed ? 'Download failed' : skipped ? 'Skipped' : loading ? 'Downloading' : 'Not downloaded yet'
  const body = failed
    ? item.error || 'The download did not finish. Retry to queue it again.'
    : skipped
      ? item.skip_reason
      : loading
        ? 'The video will be playable here when the download finishes.'
        : 'Download this video to watch it here.'

  return (
    <div className={`${frame} relative bg-muted`}>
      <img
        src={`/api/media/${item.id}/thumb`}
        alt=""
        className="absolute inset-0 h-full w-full object-cover opacity-20 blur-sm"
        onError={(e) => { e.currentTarget.style.display = 'none' }}
      />
      <div className="relative flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
        <Icon className={`h-6 w-6 ${failed ? 'text-err' : 'text-muted-foreground'} ${loading ? 'animate-spin' : ''}`} />
        <p className="text-[13px] font-semibold">{title}</p>
        <p className="max-w-md text-[13px] text-muted-foreground">{body}</p>
        {loading && progress && (
          <div className="w-full max-w-xs space-y-1">
            <ProgressBar progress={(progress.progress || 0) * 100} animated />
            {!!progress.bytes_total && (
              <p className="text-[12px] text-muted-foreground">
                {formatBytes(progress.bytes_done)} of {formatBytes(progress.bytes_total)}
              </p>
            )}
          </div>
        )}
        {failed && (
          <Button size="sm" onClick={onRetry} disabled={busy}><RotateCw className="mr-1.5 h-3.5 w-3.5" />Retry download</Button>
        )}
        {!failed && !loading && (
          <Button size="sm" onClick={onDownload} disabled={busy}><Download className="mr-1.5 h-3.5 w-3.5" />Download</Button>
        )}
      </div>
    </div>
  )
}
