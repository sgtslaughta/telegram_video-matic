import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Page, PageHeader } from '@/components/shared/PageHeader';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RugbyMatchReview } from '@/components/RugbyMatchReview';
import { HistoryTab } from '@/components/downloads/HistoryTab';
import { QueueTab } from '@/components/downloads/QueueTab';
import { WantedTab } from '@/components/downloads/WantedTab';
import { useFailed, useWanted } from '@/components/downloads/data';
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads';
import { useDownloadsTabs } from '@/hooks/useDownloadsTabs';
import { useRugbyMatches } from '@/hooks/useRugby';
import { useWebSocket } from '@/hooks/useWebSocket';
const trigger = 'rounded-none border-b-2 border-transparent bg-transparent px-3 py-2 text-[13px] data-[state=active]:border-brand data-[state=active]:bg-transparent data-[state=active]:shadow-none';
export default function Downloads() {
    useWebSocket(); // keeps live progress flowing while this page is open
    const { tab, kind, setTab, setKind } = useDownloadsTabs();
    const active = useActiveDownloads();
    const queued = useQueuedDownloads();
    const wanted = useWanted();
    const failed = useFailed();
    const review = useRugbyMatches('needs_review');
    const count = (n, label) => (n ? `${n} ${label}` : null);
    const parts = [
        count(active.data?.length, 'downloading'), count(queued.data?.length, 'queued'),
        count(wanted.data?.length, 'missing games'), count(failed.data?.length, 'failed'),
    ].filter(Boolean);
    const loading = active.isLoading || queued.isLoading;
    const badge = (n) => (n ? _jsx("span", { className: "ml-1.5 text-[11px] tabular-nums text-muted-foreground", children: n }) : null);
    return (_jsxs(Page, { wide: true, children: [_jsx(PageHeader, { title: "Downloads", description: loading ? _jsx(Skeleton, { className: "h-4 w-48" }) : parts.length ? parts.join(', ') : 'Nothing in progress.' }), _jsxs(Tabs, { value: tab, onValueChange: setTab, children: [_jsxs(TabsList, { className: "mb-4 h-auto w-full justify-start gap-1 rounded-none border-b border-border bg-transparent p-0", children: [_jsxs(TabsTrigger, { value: "queue", className: trigger, children: ["Queue", badge((active.data?.length ?? 0) + (queued.data?.length ?? 0))] }), _jsxs(TabsTrigger, { value: "wanted", className: trigger, children: ["Wanted", badge((wanted.data?.length ?? 0) + (failed.data?.length ?? 0))] }), _jsx(TabsTrigger, { value: "history", className: trigger, children: "History" }), _jsxs(TabsTrigger, { value: "review", className: trigger, children: ["Review", badge(review.data?.length)] })] }), _jsx(TabsContent, { value: "queue", className: "mt-0", children: _jsx(QueueTab, {}) }), _jsx(TabsContent, { value: "wanted", className: "mt-0", children: _jsx(WantedTab, {}) }), _jsx(TabsContent, { value: "history", className: "mt-0", children: _jsx(HistoryTab, { kind: kind, setKind: setKind }) }), _jsx(TabsContent, { value: "review", className: "mt-0", children: _jsx(RugbyMatchReview, {}) })] })] }));
}
