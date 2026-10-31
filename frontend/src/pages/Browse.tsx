import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LayoutGrid, List, Search } from 'lucide-react'
import { Page, PageHeader } from '@/components/shared/PageHeader'
import { EmptyState } from '@/components/shared/EmptyState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Combobox } from '@/components/ui/combobox'
import MediaDrawer from '@/components/MediaDrawer'
import type { BrowseMsg } from '@/components/media/BrowseItem'
import { BrowseCard, BrowseRow, BrowseSkeleton } from '@/components/media/BrowseItem'
import { useItemDownload } from '@/components/media/useItemDownload'
import { usePersistedState } from '@/hooks/usePersistedState'
import { useChannels, useTopics, useBrowse } from '@/hooks/useChannelsTopics'
import { useRugbyEnrichMessages } from '@/hooks/useRugby'
import { useListNav } from '@/hooks/useMediaTools'

type SortKey = 'date' | 'size' | 'name'
type ViewMode = 'cards' | 'list'

const STATUSES = ['all', 'available', 'queued', 'downloading', 'downloaded', 'failed', 'skipped', 'pending']
const SORTS = [
  { value: 'date', label: 'Newest first' }, { value: 'size', label: 'Largest first' }, { value: 'name', label: 'Name (A–Z)' },
]

export default function Browse() {
  const [params] = useSearchParams()
  const topbarQ = (params.get('q') ?? '').toLowerCase()

  const [channelId, setChannelId] = usePersistedState<number | null>('browse.channelId', null)
  const [topicId, setTopicId] = usePersistedState<number | null>('browse.topicId', null)
  const [view, setView] = usePersistedState<ViewMode>('browse.view', 'cards')
  const [sortKey, setSortKey] = usePersistedState<SortKey>('browse.sort', 'date')
  const [statusFilter, setStatusFilter] = usePersistedState('browse.status', 'all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<BrowseMsg | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const channels = useChannels()
  const topics = useTopics(channelId)
  const browse = useBrowse(channelId, topicId)
  const drawerDl = useItemDownload(selected ?? { tg_msg_id: 0 }, channelId ?? 0)

  const openItem = (item: BrowseMsg) => { setSelected(item); setDrawerOpen(true) }

  const allItems = useMemo(() => browse.data?.pages.flatMap((p: { items: BrowseMsg[] }) => p.items) ?? ([] as BrowseMsg[]), [browse.data])
  // Enrich the live items on screen — works for un-cached videos in any topic.
  const enrichment = useRugbyEnrichMessages(allItems)

  const items = useMemo(() => {
    const q = (search || topbarQ).toLowerCase()
    const list = allItems.filter((m: BrowseMsg) => {
      if (statusFilter !== 'all' && m.status !== statusFilter) return false
      return !q || `${m.caption ?? ''} ${m.file_name ?? ''}`.toLowerCase().includes(q)
    })
    return list.sort((a: BrowseMsg, b: BrowseMsg) => {
      if (sortKey === 'size') return (b.size_bytes ?? 0) - (a.size_bytes ?? 0)
      if (sortKey === 'name') return (a.file_name ?? '').localeCompare(b.file_name ?? '')
      return new Date(b.date_posted).getTime() - new Date(a.date_posted).getTime()
    })
  }, [allItems, statusFilter, search, topbarQ, sortKey])

  const { active, searchRef } = useListNav(items.length, (i) => openItem(items[i]))
  const rugbyOf = (i: BrowseMsg) => enrichment.data?.[String(i.tg_msg_id)]

  return (
    <Page wide>
      <PageHeader
        title="Browse"
        description="Live media from your channels. Download a video or check what a subscription would capture."
        actions={
          <div className="flex items-center gap-1">
            <Button variant={view === 'cards' ? 'secondary' : 'ghost'} size="icon" onClick={() => setView('cards')} aria-label="Card view"><LayoutGrid className="h-4 w-4" /></Button>
            <Button variant={view === 'list' ? 'secondary' : 'ghost'} size="icon" onClick={() => setView('list')} aria-label="List view"><List className="h-4 w-4" /></Button>
          </div>
        }
      />

      <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_160px_160px_minmax(0,1.2fr)]">
        <Combobox
          value={channelId?.toString() || ''}
          onChange={(v) => { setChannelId(v ? parseInt(v) : null); setTopicId(null) }}
          disabled={channels.isLoading}
          placeholder="Select a channel…"
          searchPlaceholder="Search channels…"
          options={(channels.data ?? []).map((ch) => ({ value: ch.id.toString(), label: ch.title }))}
        />
        <Combobox
          value={topicId?.toString() || 'all'}
          onChange={(v) => setTopicId(v === 'all' ? null : parseInt(v))}
          disabled={!channelId || topics.isLoading}
          placeholder="All topics"
          searchPlaceholder="Search topics…"
          options={[{ value: 'all', label: 'All topics' }, ...(topics.data ?? []).map((t) => ({ value: t.id.toString(), label: t.title }))]}
        />
        <Combobox value={statusFilter} onChange={setStatusFilter} options={STATUSES.map((s) => ({ value: s, label: s === 'all' ? 'All statuses' : s[0].toUpperCase() + s.slice(1) }))} />
        <Combobox value={sortKey} onChange={(v) => setSortKey(v as SortKey)} options={SORTS} />
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input ref={searchRef} aria-label="Search videos" placeholder="Search title or file name (/)" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
        </div>
      </div>

      {!channelId ? (
        <EmptyState title="Select a channel" message="Pick a channel above to browse its media." />
      ) : browse.isLoading ? (
        <BrowseSkeleton view={view} />
      ) : items.length === 0 ? (
        <EmptyState title="No media found" message="Try a different channel, topic, status or search." />
      ) : view === 'cards' ? (
        <div className="grid grid-cols-1 gap-3 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((item: BrowseMsg, i: number) => (
            <BrowseCard key={item.tg_msg_id} item={item} index={i} active={i === active} channelId={channelId} rugby={rugbyOf(item)} onOpen={openItem} />
          ))}
        </div>
      ) : (
        <div className="divide-y divide-border rounded-lg border bg-card">
          {items.map((item: BrowseMsg, i: number) => (
            <BrowseRow key={item.tg_msg_id} item={item} index={i} active={i === active} channelId={channelId} rugby={rugbyOf(item)} onOpen={openItem} />
          ))}
        </div>
      )}

      {channelId && browse.hasNextPage && (
        <div className="flex flex-col items-center gap-1 pt-5">
          <span className="text-[12px] text-muted-foreground">{items.length} shown</span>
          <Button variant="outline" onClick={() => browse.fetchNextPage()} disabled={browse.isFetchingNextPage}>
            {browse.isFetchingNextPage ? 'Loading…' : 'Load more'}
          </Button>
        </div>
      )}

      <MediaDrawer
        item={selected}
        channelId={channelId}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onDownload={() => void drawerDl.onDownload()}
        downloadPending={drawerDl.pending}
        rugby={selected ? rugbyOf(selected) : null}
      />
    </Page>
  )
}
