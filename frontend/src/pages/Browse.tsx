import { useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Download, LayoutGrid, List, Search } from 'lucide-react'
import { useChannels, useTopics, useBrowse } from '@/hooks/useChannelsTopics'
import { useDownloadMedia } from '@/hooks/useMedia'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import * as api from '@/lib/api'

function formatBytes(n?: number | null): string {
  if (!n || n <= 0) return '—'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), u.length - 1)
  return `${(n / 1024 ** i).toFixed(1)} ${u[i]}`
}

type SortKey = 'date' | 'size' | 'name'
type ViewMode = 'cards' | 'list'

const STATUSES = ['all', 'available', 'queued', 'downloading', 'downloaded', 'failed', 'skipped', 'pending']

export default function Browse() {
  const [params] = useSearchParams()
  const topbarQ = (params.get('q') ?? '').toLowerCase()

  const [channelId, setChannelId] = useState<number | null>(null)
  const [topicId, setTopicId] = useState<number | null>(null)
  const [view, setView] = useState<ViewMode>('cards')
  const [sortKey, setSortKey] = useState<SortKey>('date')
  const [statusFilter, setStatusFilter] = useState('all')
  const [search, setSearch] = useState('')

  const channels = useChannels()
  const topics = useTopics(channelId)
  const browse = useBrowse(channelId, topicId)

  const items = useMemo(() => {
    const q = (search || topbarQ).toLowerCase()
    let list = (browse.data ?? []).filter((m: any) => {
      if (statusFilter !== 'all' && m.status !== statusFilter) return false
      if (q && !(`${m.caption ?? ''} ${m.file_name ?? ''}`.toLowerCase().includes(q))) return false
      return true
    })
    list = [...list].sort((a: any, b: any) => {
      if (sortKey === 'size') return (b.size_bytes ?? 0) - (a.size_bytes ?? 0)
      if (sortKey === 'name') return (a.file_name ?? '').localeCompare(b.file_name ?? '')
      return new Date(b.date_posted).getTime() - new Date(a.date_posted).getTime()
    })
    return list
  }, [browse.data, statusFilter, search, topbarQ, sortKey])

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Browse Media</h1>
        <p className="mt-1 text-sm text-muted-foreground">Live media from your channels — download or see what a subscription captures</p>
      </div>

      <Card>
        <CardContent className="grid gap-4 pt-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label>Channel</Label>
            <Select
              value={channelId?.toString() || ''}
              onValueChange={(v) => { setChannelId(v ? parseInt(v) : null); setTopicId(null) }}
              disabled={channels.isLoading}
            >
              <SelectTrigger><SelectValue placeholder="Select a channel…" /></SelectTrigger>
              <SelectContent>
                {channels.data?.map((ch) => (
                  <SelectItem key={ch.id} value={ch.id.toString()}>{ch.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Topic</Label>
            <Select
              value={topicId?.toString() || 'all'}
              onValueChange={(v) => setTopicId(v === 'all' ? null : parseInt(v))}
              disabled={!channelId || topics.isLoading}
            >
              <SelectTrigger><SelectValue placeholder="All topics" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All topics</SelectItem>
                {topics.data?.map((t) => (
                  <SelectItem key={t.id} value={t.id.toString()}>{t.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Status</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>{s === 'all' ? 'All statuses' : s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Sort by</Label>
            <Select value={sortKey} onValueChange={(v) => setSortKey(v as SortKey)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="date">Newest first</SelectItem>
                <SelectItem value="size">Largest first</SelectItem>
                <SelectItem value="name">Name (A–Z)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search title / filename…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
        </div>
        <div className="ml-auto flex items-center gap-1">
          <span className="mr-2 text-sm text-muted-foreground">{items.length} items</span>
          <Button variant={view === 'cards' ? 'secondary' : 'ghost'} size="icon" onClick={() => setView('cards')} aria-label="Card view"><LayoutGrid className="h-4 w-4" /></Button>
          <Button variant={view === 'list' ? 'secondary' : 'ghost'} size="icon" onClick={() => setView('list')} aria-label="List view"><List className="h-4 w-4" /></Button>
        </div>
      </div>

      {!channelId ? (
        <EmptyState title="Select a channel" message="Choose a channel above to browse its media" />
      ) : browse.isLoading ? (
        <div className="py-12 text-center text-muted-foreground">Loading media from Telegram…</div>
      ) : items.length === 0 ? (
        <EmptyState title="No media found" message="Try a different channel, topic, status, or search" />
      ) : view === 'cards' ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {items.map((item: any) => <MediaCard key={item.tg_msg_id} item={item} channelId={channelId} />)}
        </div>
      ) : (
        <Card><div className="divide-y divide-border">
          {items.map((item: any) => <MediaRow key={item.tg_msg_id} item={item} channelId={channelId} />)}
        </div></Card>
      )}
    </div>
  )
}

function useItemDownload(item: any, channelId: number) {
  const qc = useQueryClient()
  const dl = useDownloadMedia(item.media_id ?? 0)
  const [adhocPending, setAdhocPending] = useState(false)
  const onDownload = async () => {
    if (item.media_id) { dl.mutate(); return }
    try {
      setAdhocPending(true)
      await api.channels.browseDownload(channelId, item.tg_msg_id)
      toast.success('Queued for download')
      qc.invalidateQueries({ queryKey: ['browse'] })
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Download failed')
    } finally {
      setAdhocPending(false)
    }
  }
  return { onDownload, pending: dl.isPending || adhocPending }
}

function MediaCard({ item, channelId }: { item: any; channelId: number }) {
  const navigate = useNavigate()
  const { onDownload, pending } = useItemDownload(item, channelId)
  return (
    <Card className="flex h-full flex-col transition-shadow hover:shadow-md">
      <button
        onClick={() => item.media_id && navigate(`/media/${item.media_id}`)}
        className="w-full overflow-hidden rounded-t-lg transition-opacity hover:opacity-80"
      >
        <MediaThumb src={api.channels.browseThumbUrl(channelId, item.tg_msg_id)} alt={item.caption || 'Media'} size="md" />
      </button>
      <CardContent className="flex flex-1 flex-col gap-2 p-3">
        <p className="line-clamp-2 text-xs text-foreground">{item.caption || item.file_name || 'Untitled'}</p>
        {item.subscription_label && (
          <p className="truncate text-[10px] text-muted-foreground">↳ {item.subscription_label}</p>
        )}
        <div className="mt-auto flex items-center justify-between">
          <StatusBadge status={item.status} />
          <span className="text-xs text-muted-foreground">{formatBytes(item.size_bytes)}</span>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" onClick={onDownload} disabled={pending}><Download className="h-3 w-3" /></Button>
            </TooltipTrigger>
            <TooltipContent>Download</TooltipContent>
          </Tooltip>
        </div>
      </CardContent>
    </Card>
  )
}

function MediaRow({ item, channelId }: { item: any; channelId: number }) {
  const navigate = useNavigate()
  const { onDownload, pending } = useItemDownload(item, channelId)
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50">
      <button onClick={() => item.media_id && navigate(`/media/${item.media_id}`)} className="h-10 w-16 shrink-0 overflow-hidden rounded">
        <MediaThumb src={api.channels.browseThumbUrl(channelId, item.tg_msg_id)} alt={item.caption || 'Media'} size="sm" />
      </button>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm">{item.caption || item.file_name || 'Untitled'}</p>
        <p className="text-xs text-muted-foreground">
          {new Date(item.date_posted).toLocaleDateString()}
          {item.subscription_label ? ` · ↳ ${item.subscription_label}` : ''}
        </p>
      </div>
      <span className="hidden w-20 text-right text-xs text-muted-foreground sm:inline">{formatBytes(item.size_bytes)}</span>
      <StatusBadge status={item.status} />
      <Button size="sm" variant="ghost" onClick={onDownload} disabled={pending} aria-label="Download"><Download className="h-4 w-4" /></Button>
    </div>
  )
}
