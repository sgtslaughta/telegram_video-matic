import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { LayoutGrid, List, Search } from 'lucide-react';
import { Page, PageHeader } from '@/components/shared/PageHeader';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Combobox } from '@/components/ui/combobox';
import MediaDrawer from '@/components/MediaDrawer';
import { BrowseCard, BrowseRow, BrowseSkeleton } from '@/components/media/BrowseItem';
import { useItemDownload } from '@/components/media/useItemDownload';
import { usePersistedState } from '@/hooks/usePersistedState';
import { useChannels, useTopics, useBrowse } from '@/hooks/useChannelsTopics';
import { useRugbyEnrichMessages } from '@/hooks/useRugby';
import { useListNav } from '@/hooks/useMediaTools';
const STATUSES = ['all', 'available', 'queued', 'downloading', 'downloaded', 'failed', 'skipped', 'pending'];
const SORTS = [
    { value: 'date', label: 'Newest first' }, { value: 'size', label: 'Largest first' }, { value: 'name', label: 'Name (A–Z)' },
];
export default function Browse() {
    const [params] = useSearchParams();
    const topbarQ = (params.get('q') ?? '').toLowerCase();
    const [channelId, setChannelId] = usePersistedState('browse.channelId', null);
    const [topicId, setTopicId] = usePersistedState('browse.topicId', null);
    const [view, setView] = usePersistedState('browse.view', 'cards');
    const [sortKey, setSortKey] = usePersistedState('browse.sort', 'date');
    const [statusFilter, setStatusFilter] = usePersistedState('browse.status', 'all');
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState(null);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const channels = useChannels();
    const topics = useTopics(channelId);
    const browse = useBrowse(channelId, topicId);
    const drawerDl = useItemDownload(selected ?? { tg_msg_id: 0 }, channelId ?? 0);
    const openItem = (item) => { setSelected(item); setDrawerOpen(true); };
    const allItems = useMemo(() => browse.data?.pages.flatMap((p) => p.items) ?? [], [browse.data]);
    // Enrich the live items on screen — works for un-cached videos in any topic.
    const enrichment = useRugbyEnrichMessages(allItems);
    const items = useMemo(() => {
        const q = (search || topbarQ).toLowerCase();
        const list = allItems.filter((m) => {
            if (statusFilter !== 'all' && m.status !== statusFilter)
                return false;
            return !q || `${m.caption ?? ''} ${m.file_name ?? ''}`.toLowerCase().includes(q);
        });
        return list.sort((a, b) => {
            if (sortKey === 'size')
                return (b.size_bytes ?? 0) - (a.size_bytes ?? 0);
            if (sortKey === 'name')
                return (a.file_name ?? '').localeCompare(b.file_name ?? '');
            return new Date(b.date_posted).getTime() - new Date(a.date_posted).getTime();
        });
    }, [allItems, statusFilter, search, topbarQ, sortKey]);
    const { active, searchRef } = useListNav(items.length, (i) => openItem(items[i]));
    const rugbyOf = (i) => enrichment.data?.[String(i.tg_msg_id)];
    return (_jsxs(Page, { wide: true, children: [_jsx(PageHeader, { title: "Browse", description: "Live media from your channels. Download a video or check what a subscription would capture.", actions: _jsxs("div", { className: "flex items-center gap-1", children: [_jsx(Button, { variant: view === 'cards' ? 'secondary' : 'ghost', size: "icon", onClick: () => setView('cards'), "aria-label": "Card view", children: _jsx(LayoutGrid, { className: "h-4 w-4" }) }), _jsx(Button, { variant: view === 'list' ? 'secondary' : 'ghost', size: "icon", onClick: () => setView('list'), "aria-label": "List view", children: _jsx(List, { className: "h-4 w-4" }) })] }) }), _jsxs("div", { className: "mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_160px_160px_minmax(0,1.2fr)]", children: [_jsx(Combobox, { value: channelId?.toString() || '', onChange: (v) => { setChannelId(v ? parseInt(v) : null); setTopicId(null); }, disabled: channels.isLoading, placeholder: "Select a channel\u2026", searchPlaceholder: "Search channels\u2026", options: (channels.data ?? []).map((ch) => ({ value: ch.id.toString(), label: ch.title })) }), _jsx(Combobox, { value: topicId?.toString() || 'all', onChange: (v) => setTopicId(v === 'all' ? null : parseInt(v)), disabled: !channelId || topics.isLoading, placeholder: "All topics", searchPlaceholder: "Search topics\u2026", options: [{ value: 'all', label: 'All topics' }, ...(topics.data ?? []).map((t) => ({ value: t.id.toString(), label: t.title }))] }), _jsx(Combobox, { value: statusFilter, onChange: setStatusFilter, options: STATUSES.map((s) => ({ value: s, label: s === 'all' ? 'All statuses' : s[0].toUpperCase() + s.slice(1) })) }), _jsx(Combobox, { value: sortKey, onChange: (v) => setSortKey(v), options: SORTS }), _jsxs("div", { className: "relative", children: [_jsx(Search, { className: "pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" }), _jsx(Input, { ref: searchRef, "aria-label": "Search videos", placeholder: "Search title or file name (/)", value: search, onChange: (e) => setSearch(e.target.value), className: "pl-8" })] })] }), !channelId ? (_jsx(EmptyState, { title: "Select a channel", message: "Pick a channel above to browse its media." })) : browse.isLoading ? (_jsx(BrowseSkeleton, { view: view })) : items.length === 0 ? (_jsx(EmptyState, { title: "No media found", message: "Try a different channel, topic, status or search." })) : view === 'cards' ? (_jsx("div", { className: "grid grid-cols-1 gap-3 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4", children: items.map((item, i) => (_jsx(BrowseCard, { item: item, index: i, active: i === active, channelId: channelId, rugby: rugbyOf(item), onOpen: openItem }, item.tg_msg_id))) })) : (_jsx("div", { className: "divide-y divide-border rounded-lg border bg-card", children: items.map((item, i) => (_jsx(BrowseRow, { item: item, index: i, active: i === active, channelId: channelId, rugby: rugbyOf(item), onOpen: openItem }, item.tg_msg_id))) })), channelId && browse.hasNextPage && (_jsxs("div", { className: "flex flex-col items-center gap-1 pt-5", children: [_jsxs("span", { className: "text-[12px] text-muted-foreground", children: [items.length, " shown"] }), _jsx(Button, { variant: "outline", onClick: () => browse.fetchNextPage(), disabled: browse.isFetchingNextPage, children: browse.isFetchingNextPage ? 'Loading…' : 'Load more' })] })), _jsx(MediaDrawer, { item: selected, channelId: channelId, open: drawerOpen, onOpenChange: setDrawerOpen, onDownload: () => void drawerDl.onDownload(), downloadPending: drawerDl.pending, rugby: selected ? rugbyOf(selected) : null })] }));
}
