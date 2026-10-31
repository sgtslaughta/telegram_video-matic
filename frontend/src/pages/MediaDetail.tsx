import { Link, useNavigate, useParams } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { Page } from '@/components/shared/PageHeader'
import { RugbyTag } from '@/components/shared/RugbyTag'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { MediaPlayer } from '@/components/media/MediaPlayer'
import { HistoryTimeline } from '@/components/media/HistoryTimeline'
import { useDownloadMedia, useRequeueMedia } from '@/hooks/useMedia'
import { useActiveDownloads } from '@/hooks/useDownloads'
import { useRugbyEnrichmentByMedia } from '@/hooks/useRugby'
import { useMediaFull, useMediaHistory, useSetKeep } from '@/hooks/useMediaTools'
import { absTime, formatBytes, formatDuration } from '@/lib/format'
import { withToast } from '@/lib/toast'

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border bg-card">
      <h2 className="flex h-11 items-center border-b px-4 text-[13px] font-semibold">{title}</h2>
      {children}
    </section>
  )
}

function Loading() {
  return (
    <Page>
      <Skeleton className="mb-4 h-4 w-16" />
      <Skeleton className="aspect-video w-full rounded-lg" />
      <Skeleton className="mt-5 h-7 w-1/2" />
      <Skeleton className="mt-2 h-4 w-2/3" />
    </Page>
  )
}

export default function MediaDetail() {
  const id = parseInt(useParams<{ id: string }>().id || '0', 10)
  const navigate = useNavigate()
  const qc = useQueryClient()
  const media = useMediaFull(id)
  const history = useMediaHistory(id)
  const downloads = useActiveDownloads()
  const download = useDownloadMedia(id)
  const requeue = useRequeueMedia(id)
  const setKeep = useSetKeep(id)
  const rugby = useRugbyEnrichmentByMedia(id > 0 ? [id] : []).data?.[String(id)]

  if (media.isLoading) return <Loading />
  if (media.error || !media.data) {
    return (
      <Page>
        <div className="rounded-lg bg-err/10 p-4 text-[13px] text-err">
          Could not load this video. <Link to="/browse" className="underline">Back to browse</Link>
        </div>
      </Page>
    )
  }

  const item = media.data
  const live = downloads.data?.find((d) => d.media_id === id)
  const title = rugby ? `${rugby.home} vs ${rugby.away}` : item.caption?.split('\n')[0] || item.file_name || `Video ${id}`
  const matchDate = item.content_date ?? item.date_posted
  const reactions = Object.entries((item.reactions ?? {}) as Record<string, number>)
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['media'] })
    qc.invalidateQueries({ queryKey: ['events'] })
  }
  const toggleKeep = (keep: boolean) =>
    withToast(() => setKeep.mutateAsync(keep), {
      success: keep ? 'Keeping this video forever' : 'Video can be cleaned up again',
      undo: () => setKeep.mutateAsync(!keep),
    })

  const meta = [
    rugby?.league, rugby?.round && `Round ${rugby.round}`,
    matchDate && <span key="d" title={absTime(matchDate)}>{new Date(matchDate).toLocaleDateString()}</span>,
    item.size_bytes ? formatBytes(item.size_bytes) : null,
    formatDuration(item.duration_sec),
  ].filter(Boolean)

  return (
    <Page>
      <button
        onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/browse'))}
        className="mb-4 inline-flex items-center gap-1 text-[13px] text-brand hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />Back
      </button>

      <MediaPlayer
        item={item}
        progress={live}
        busy={download.isPending || requeue.isPending}
        onDownload={() => withToast(() => download.mutateAsync(), { success: 'Download queued' }).then(refresh)}
        onRetry={() => withToast(() => requeue.mutateAsync(), { success: 'Download queued again' }).then(refresh)}
      />

      <div className="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="break-words text-[20px] font-semibold leading-7 tracking-tight">{title}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] text-muted-foreground">
            <StatusBadge status={item.status} />
            {meta.map((m, i) => <span key={i} className="flex items-center gap-2">{i > 0 && <span aria-hidden>·</span>}{m}</span>)}
          </div>
          {rugby && <RugbyTag rugby={rugby} className="mt-2 text-[12px] text-muted-foreground" />}
        </div>
        <label className="flex items-center gap-2 text-[13px]">
          <Switch checked={!!item.keep} onCheckedChange={toggleKeep} disabled={setKeep.isPending} aria-label="Keep forever" />
          Keep forever
        </label>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="space-y-4">
          {item.caption && (
            <Panel title="Caption"><p className="whitespace-pre-wrap p-4 text-[13px]">{item.caption}</p></Panel>
          )}
          <Panel title="Details">
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 p-4 text-[13px]">
              {item.file_name && (<><dt className="text-muted-foreground">File</dt><dd className="break-all">{item.file_name}</dd></>)}
              {item.local_path && (<><dt className="text-muted-foreground">Saved to</dt><dd className="break-all">{item.local_path}</dd></>)}
              {item.mime && (<><dt className="text-muted-foreground">Type</dt><dd>{item.mime}</dd></>)}
              <dt className="text-muted-foreground">Posted</dt><dd title={absTime(item.date_posted)}>{new Date(item.date_posted).toLocaleDateString()}</dd>
              {reactions.length > 0 && (<><dt className="text-muted-foreground">Reactions</dt>
                <dd className="flex flex-wrap gap-1.5">{reactions.map(([e, n]) => <span key={e} className="rounded-full bg-muted px-2 text-[12px]">{e} {n}</span>)}</dd></>)}
              {!!item.comments_count && (<><dt className="text-muted-foreground">Comments</dt><dd>{item.comments_count}</dd></>)}
            </dl>
          </Panel>
        </div>
        <Panel title="History"><HistoryTimeline entries={history.data} loading={history.isLoading} /></Panel>
      </div>
    </Page>
  )
}
