import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Page, PageHeader } from '@/components/shared/PageHeader';
import { SubscriptionRow } from '@/components/subscriptions/SubscriptionRow';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { useChannels } from '@/hooks/useChannels';
import { useOverview } from '@/hooks/useOverview';
import { useDeleteSubscription, useScanSubscription, useSubscriptions } from '@/hooks/useSubscriptions';
import { withToast } from '@/lib/toast';
const isTyping = (t) => t instanceof HTMLElement && (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) || t.getAttribute('role') === 'switch');
function DeleteConfirm({ id, onDone }) {
    const del = useDeleteSubscription(id ?? 0);
    return (_jsx(ConfirmDialog, { isOpen: id !== null, title: "Delete subscription", confirmText: "Delete", cancelText: "Cancel", description: "The subscription stops syncing. Files already downloaded are kept.", onCancel: onDone, onConfirm: async () => { await withToast(() => del.mutateAsync(), { success: 'Subscription deleted' }); onDone(); } }));
}
function ScanRunner({ id, onDone }) {
    const scan = useScanSubscription(id);
    const ran = useRef(false);
    useEffect(() => {
        if (ran.current)
            return;
        ran.current = true;
        void withToast(() => scan.mutateAsync(), { success: 'Scan started' }).then(onDone);
    }, [scan, onDone]);
    return null;
}
export default function SubscriptionsList() {
    const navigate = useNavigate();
    const [search, setSearch] = useState('');
    const [active, setActive] = useState(0);
    const [deleteId, setDeleteId] = useState(null);
    const [scanId, setScanId] = useState(null);
    const rows = useRef([]);
    const { data: subs = [], isLoading } = useSubscriptions();
    const { data: channels } = useChannels();
    const { data: overview } = useOverview(24);
    const chanTitle = (id) => channels?.find((c) => c.id === id)?.title ?? `Channel ${id}`;
    const q = search.toLowerCase();
    const visible = subs.filter((s) => !q || [s.name, s.channel_title, s.topic_title, chanTitle(s.channel_id)].some((v) => v?.toLowerCase().includes(q)));
    const move = useCallback((to) => {
        const i = Math.max(0, Math.min(to, visible.length - 1));
        setActive(i);
        rows.current[i]?.focus();
    }, [visible.length]);
    useEffect(() => {
        const h = (e) => {
            if (e.metaKey || e.ctrlKey || e.altKey || isTyping(e.target) || !visible.length)
                return;
            if (e.key === 'j')
                move(active + 1);
            else if (e.key === 'k')
                move(active - 1);
            else if (e.key === 'e')
                navigate(`/subscriptions/${visible[Math.min(active, visible.length - 1)].id}`);
        };
        window.addEventListener('keydown', h);
        return () => window.removeEventListener('keydown', h);
    }, [active, move, navigate, visible]);
    return (_jsxs(Page, { wide: true, children: [_jsx(PageHeader, { title: "Subscriptions", description: subs.length ? `${subs.filter((s) => s.enabled).length} of ${subs.length} active` : undefined, actions: _jsxs(Button, { onClick: () => navigate('/subscriptions/new'), children: [_jsx(Plus, { className: "mr-1.5 h-4 w-4" }), "New subscription"] }) }), subs.length > 3 && (_jsxs("div", { className: "relative mb-3 max-w-sm", children: [_jsx(Search, { className: "absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" }), _jsx(Input, { placeholder: "Search subscriptions", "aria-label": "Search subscriptions", value: search, onChange: (e) => setSearch(e.target.value), className: "pl-8" })] })), isLoading ? (_jsx("div", { className: "space-y-2", children: [0, 1, 2, 3].map((i) => _jsx(Skeleton, { className: "h-12 w-full" }, i)) })) : visible.length === 0 ? (_jsx("p", { className: "rounded-lg border border-border bg-card py-10 text-center text-[13px] text-muted-foreground", children: subs.length ? 'No subscriptions match your search.' : 'No subscriptions yet. Create one to start downloading a channel.' })) : (_jsx("div", { className: "overflow-x-auto rounded-lg border border-border bg-card", children: _jsxs("table", { className: "w-full text-[13px]", children: [_jsx("thead", { children: _jsxs("tr", { className: "h-9 border-b border-border text-left text-[12px] font-normal text-muted-foreground", children: [_jsx("th", { className: "pl-4 pr-3 font-normal", children: "Subscription" }), _jsx("th", { className: "hidden px-3 font-normal md:table-cell", children: "Frequency" }), _jsx("th", { className: "hidden px-3 font-normal lg:table-cell", children: "Filter" }), _jsx("th", { className: "hidden px-3 text-right font-normal lg:table-cell", children: "Downloaded" }), _jsx("th", { className: "hidden px-3 text-right font-normal md:table-cell", children: "Last synced" }), _jsx("th", { className: "hidden px-3 font-normal xl:table-cell", children: "New, 24h" }), _jsx("th", { className: "px-3 font-normal", children: "Enabled" }), _jsx("th", { className: "w-10" })] }) }), _jsx("tbody", { children: visible.map((s, i) => {
                                const name = s.name || s.channel_title || chanTitle(s.channel_id);
                                const detail = [s.name ? s.channel_title || chanTitle(s.channel_id) : null, s.topic_title || (s.topic_id ? `Topic ${s.topic_id}` : null)].filter(Boolean).join(' / ');
                                return (_jsx(SubscriptionRow, { ref: (el) => { rows.current[i] = el; }, sub: s, title: name, detail: detail, pulse: overview?.subscriptions.find((o) => o.id === s.id), focused: i === active, onFocus: () => setActive(i), onOpen: () => navigate(`/subscriptions/${s.id}`), onDelete: () => setDeleteId(s.id), onScan: () => setScanId(s.id) }, s.id));
                            }) })] }) })), _jsx(DeleteConfirm, { id: deleteId, onDone: () => setDeleteId(null) }), scanId !== null && _jsx(ScanRunner, { id: scanId, onDone: () => setScanId(null) }, scanId)] }));
}
