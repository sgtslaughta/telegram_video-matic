import { useQuery } from '@tanstack/react-query'
import { Download, MessageSquare, X } from 'lucide-react'
import { Drawer, DrawerContent, DrawerTitle, DrawerClose } from '@/components/ui/drawer'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/shared/StatusBadge'
import * as api from '@/lib/api'

function fmtBytes(n?: number | null): string {
  if (!n || n <= 0) return '—'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), u.length - 1)
  return `${(n / 1024 ** i).toFixed(1)} ${u[i]}`
}

function fmtDuration(sec?: number | null): string {
  if (!sec || sec <= 0) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}` : `${m}:${String(s).padStart(2, '0')}`
}

interface Props {
  item: any | null
  channelId: number | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onDownload: () => void
  downloadPending: boolean
}

export default function MediaDrawer({ item, channelId, open, onOpenChange, onDownload, downloadPending }: Props) {
  const detail = useQuery({
    queryKey: ['message', channelId, item?.tg_msg_id],
    queryFn: () => api.channels.messageDetail(channelId!, item!.tg_msg_id),
    enabled: open && !!item && !!channelId,
    staleTime: 60_000,
  })

  const title = item?.caption || item?.file_name || 'Untitled'

  return (
    <Drawer direction="right" open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="overflow-y-auto p-0">
        <DrawerClose className="absolute right-3 top-3 z-10 rounded-full bg-background/80 p-1.5 opacity-80 backdrop-blur transition-opacity hover:opacity-100">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DrawerClose>
        {item && channelId && (
          <>
            <img
              src={api.channels.browseThumbUrl(channelId, item.tg_msg_id)}
              alt={title}
              className="h-48 w-full bg-muted object-cover"
              onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
            />
            <div className="space-y-5 px-6 pb-6">
              <div className="space-y-2">
                <DrawerTitle className="pr-8 leading-snug">{title}</DrawerTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  {item.subscription_label && (
                    <span className="truncate text-xs text-muted-foreground">↳ {item.subscription_label}</span>
                  )}
                </div>
              </div>

              <Button onClick={onDownload} disabled={downloadPending} className="w-full">
                <Download className="mr-2 h-4 w-4" />
                {downloadPending ? 'Queuing…' : 'Download'}
              </Button>

              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <Meta label="Posted" value={item.date_posted ? new Date(item.date_posted).toLocaleString() : '—'} />
                <Meta label="Size" value={fmtBytes(item.size_bytes)} />
                <Meta label="Duration" value={fmtDuration(detail.data?.duration_sec ?? item.duration_sec)} />
                <Meta label="Type" value={item.mime || detail.data?.mime || '—'} />
                {item.file_name && <Meta label="Filename" value={item.file_name} span />}
              </dl>

              {item.caption && (
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase text-muted-foreground">Caption</p>
                  <p className="whitespace-pre-wrap text-sm">{item.caption}</p>
                </div>
              )}

              {/* Reactions */}
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase text-muted-foreground">Reactions</p>
                {detail.isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading…</p>
                ) : detail.data?.reactions.length ? (
                  <div className="flex flex-wrap gap-2">
                    {detail.data.reactions.map((r) => (
                      <span key={r.emoji} className="rounded-full border px-2.5 py-1 text-sm">
                        {r.emoji} {r.count}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No reactions</p>
                )}
              </div>

              {/* Comments */}
              <div className="space-y-2">
                <p className="flex items-center gap-1.5 text-xs font-medium uppercase text-muted-foreground">
                  <MessageSquare className="h-3.5 w-3.5" /> Comments
                  {detail.data?.comments.length ? ` (${detail.data.comments.length})` : ''}
                </p>
                {detail.isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading…</p>
                ) : detail.data?.comments.length ? (
                  <ul className="space-y-3">
                    {detail.data.comments.map((c) => (
                      <li key={c.id} className="rounded-md border p-3">
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-sm font-medium">{c.author}</span>
                          {c.date && (
                            <span className="text-xs text-muted-foreground">{new Date(c.date).toLocaleDateString()}</span>
                          )}
                        </div>
                        <p className="whitespace-pre-wrap text-sm text-muted-foreground">{c.text}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No comments</p>
                )}
              </div>
            </div>
          </>
        )}
      </DrawerContent>
    </Drawer>
  )
}

function Meta({ label, value, span }: { label: string; value: string; span?: boolean }) {
  return (
    <div className={span ? 'col-span-2' : ''}>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="truncate">{value}</dd>
    </div>
  )
}
