import { Download, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { RugbyTag } from '@/components/shared/RugbyTag'
import { RugbyMatchup } from '@/components/shared/RugbyMatchup'
import { useItemDownload } from './useItemDownload'
import { formatBytes } from '@/lib/format'
import type { RugbyEnrichment } from '@/lib/types'
import * as api from '@/lib/api'

/** Browse message as returned by the channel browse endpoint. */
export interface BrowseMsg {
  tg_msg_id: number
  media_id?: number | null
  caption?: string | null
  file_name?: string | null
  status: string
  size_bytes?: number | null
  date_posted: string
  subscription_label?: string | null
  [k: string]: unknown
}

interface ItemProps {
  item: BrowseMsg
  channelId: number
  rugby?: RugbyEnrichment | null
  index: number
  active: boolean
  onOpen: (i: BrowseMsg) => void
}

const title = (i: BrowseMsg) => i.caption || i.file_name || 'Untitled'
const ring = (a: boolean) => (a ? 'ring-2 ring-brand/60' : '')

function DownloadButton({ item, channelId }: { item: BrowseMsg; channelId: number }) {
  const { onDownload, pending } = useItemDownload(item, channelId)
  return (
    <Button
      size="icon" variant="ghost" className="h-8 w-8" aria-label="Download" title="Download"
      disabled={pending || item.status === 'downloaded'}
      onClick={(e) => { e.stopPropagation(); void onDownload() }}
    >
      <Download className="h-4 w-4" />
    </Button>
  )
}

export function BrowseCard({ item, channelId, rugby, index, active, onOpen }: ItemProps) {
  return (
    <article
      data-nav={index}
      role="button"
      tabIndex={0}
      onClick={() => onOpen(item)}
      onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onOpen(item) } }}
      className={`flex cursor-pointer flex-col overflow-hidden rounded-lg border bg-card transition-colors hover:bg-accent/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring ${ring(active)}`}
    >
      <div className="aspect-video w-full overflow-hidden bg-muted">
        <MediaThumb src={api.channels.browseThumbUrl(channelId, item.tg_msg_id)} alt="" size="lg" className="!h-full !w-full !rounded-none" />
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-3">
        {rugby ? (
          <>
            <RugbyMatchup rugby={rugby} size="sm" />
            <div className="flex flex-wrap items-center justify-center gap-1.5 text-[11px] text-muted-foreground">
              {rugby.round && <span className="rounded bg-brand/10 px-1.5 text-brand">R{rugby.round}</span>}
              {rugby.venue && <span className="inline-flex items-center gap-0.5"><MapPin className="h-3 w-3" />{rugby.venue}</span>}
            </div>
          </>
        ) : (
          <p className="line-clamp-2 text-[13px]">{title(item)}</p>
        )}
        {item.subscription_label && <p className="truncate text-[12px] text-muted-foreground">{item.subscription_label}</p>}
        <div className="mt-auto flex items-center gap-2 pt-1">
          <StatusBadge status={item.status} />
          <span className="text-[12px] text-muted-foreground">{item.size_bytes ? formatBytes(item.size_bytes) : ''}</span>
          <span className="ml-auto"><DownloadButton item={item} channelId={channelId} /></span>
        </div>
      </div>
    </article>
  )
}

export function BrowseRow({ item, channelId, rugby, index, active, onOpen }: ItemProps) {
  return (
    <div
      data-nav={index}
      className={`flex min-h-14 items-center gap-3 px-3 py-2 transition-colors hover:bg-accent/60 ${ring(active)}`}
    >
      <button onClick={() => onOpen(item)} className="h-10 w-[72px] shrink-0 overflow-hidden rounded-md bg-muted" aria-label={`Open ${title(item)}`}>
        <MediaThumb src={api.channels.browseThumbUrl(channelId, item.tg_msg_id)} alt="" size="sm" className="!h-full !w-full" />
      </button>
      <button onClick={() => onOpen(item)} className="min-w-0 flex-1 text-left">
        <p className="truncate text-[13px] hover:underline">{title(item)}</p>
        <p className="flex items-center gap-1 truncate text-[12px] text-muted-foreground">
          <span className="shrink-0">{new Date(item.date_posted).toLocaleDateString()}</span>
          {item.subscription_label && <span className="shrink-0">· {item.subscription_label}</span>}
          {rugby && <RugbyTag rugby={rugby} className="min-w-0" />}
        </p>
      </button>
      <span className="hidden w-20 text-right text-[12px] text-muted-foreground sm:inline">{item.size_bytes ? formatBytes(item.size_bytes) : ''}</span>
      <StatusBadge status={item.status} />
      <DownloadButton item={item} channelId={channelId} />
    </div>
  )
}

export function BrowseSkeleton({ view }: { view: 'cards' | 'list' }) {
  const n = 8
  return view === 'cards' ? (
    <div className="grid grid-cols-1 gap-3 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" aria-busy="true">
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="overflow-hidden rounded-lg border bg-card">
          <div className="aspect-video animate-pulse bg-muted" />
          <div className="space-y-2 p-3"><div className="h-3.5 w-4/5 animate-pulse rounded bg-muted" /><div className="h-3 w-1/2 animate-pulse rounded bg-muted" /></div>
        </div>
      ))}
    </div>
  ) : (
    <div className="divide-y rounded-lg border bg-card" aria-busy="true">
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="flex h-14 items-center gap-3 px-3">
          <div className="h-10 w-[72px] animate-pulse rounded-md bg-muted" />
          <div className="h-3.5 w-1/2 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}
