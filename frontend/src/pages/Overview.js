import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { Page, PageHeader } from '@/components/shared/PageHeader';
import { Skeleton } from '@/components/ui/skeleton';
import { SyncPulse, PulseLegend } from '@/components/overview/SyncPulse';
import { StatTile } from '@/components/shared/Sparkline';
import { DownloadingNow } from '@/components/overview/DownloadingNow';
import { Thumb } from '@/components/shared/Thumb';
import { useOverview } from '@/hooks/useOverview';
import { usePersistedState } from '@/hooks/usePersistedState';
import { absTime, formatBytes, formatDuration, relTime } from '@/lib/format';
import { cn } from '@/lib/utils';
function healthLine(o) {
    if (o.telegram.status === 'disconnected')
        return 'Telegram is disconnected. Sync resumes automatically once it reconnects.';
    if (o.telegram.status === 'unconfigured')
        return 'Connect a Telegram account to start syncing.';
    const n = o.subscriptions.filter((s) => s.enabled).length;
    return `${n} active subscription${n === 1 ? '' : 's'}, last synced ${relTime(o.telegram.last_ok_poll_at)}.`;
}
function Section({ title, aside, children, className }) {
    return (_jsxs("section", { className: cn('min-w-0 rounded-lg border border-border bg-card', className), children: [_jsxs("div", { className: "flex h-11 items-center justify-between border-b border-border px-4", children: [_jsx("h2", { className: "text-[13px] font-semibold", children: title }), aside] }), _jsx("div", { className: "px-4", children: children })] }));
}
function RangeToggle({ value, onChange }) {
    return (_jsx("div", { role: "radiogroup", "aria-label": "Range", className: "flex rounded-md border border-border p-0.5 text-[12px]", children: [[24, '24h'], [168, '7d']].map(([h, l]) => (_jsx("button", { role: "radio", "aria-checked": value === h, onClick: () => onChange(h), className: cn('rounded px-2 py-0.5 transition-colors', value === h ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:text-foreground'), children: l }, h))) }));
}
function ArrivalRow({ a }) {
    return (_jsx("li", { children: _jsxs(Link, { to: `/media/${a.id}`, className: "-mx-2 flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-accent/60", children: [_jsx(Thumb, { id: a.id, className: "h-9 w-16 shrink-0" }), _jsxs("div", { className: "min-w-0 flex-1", children: [_jsx("p", { className: "truncate text-[13px] font-medium", children: a.title }), _jsx("p", { className: "truncate text-[12px] text-muted-foreground", children: [a.subtitle, formatDuration(a.duration_sec), a.size_bytes ? formatBytes(a.size_bytes) : null].filter(Boolean).join(', ') })] }), _jsx("span", { className: "shrink-0 text-[12px] text-muted-foreground", title: absTime(a.at), children: relTime(a.at) })] }) }));
}
function AttentionRow({ to, count, label, tone }) {
    return (_jsx("li", { children: _jsxs(Link, { to: to, className: "-mx-2 flex items-center gap-3 rounded-md px-2 py-2 text-[13px] transition-colors hover:bg-accent/60", children: [_jsx("span", { className: cn('h-2 w-2 rounded-full', tone === 'err' ? 'bg-err' : 'bg-warn') }), _jsx("span", { className: "flex-1", children: label }), _jsx("span", { className: "tabular-nums text-muted-foreground", children: count }), _jsx(ChevronRight, { className: "h-4 w-4 text-muted-foreground" })] }) }));
}
export default function Overview() {
    const [hours, setHours] = usePersistedState('overview.hours', 24);
    const { data, isLoading, error } = useOverview(hours);
    if (error) {
        return (_jsxs(Page, { children: [_jsx(PageHeader, { title: "Overview" }), _jsxs("p", { className: "text-[13px] text-muted-foreground", children: ["The overview couldn\u2019t load (", String(error.message), "). It retries every 30 seconds."] })] }));
    }
    const att = data?.attention;
    const attention = att ? [
        att.failed > 0 && _jsx(AttentionRow, { to: "/downloads?tab=wanted", count: att.failed, label: "Downloads failed", tone: "err" }, "f"),
        att.cleanup_paused && _jsx(AttentionRow, { to: "/storage", count: att.cleanup_paused.count, label: `Cleanup waiting for approval (${att.cleanup_paused.gb} GB)`, tone: "warn" }, "c"),
        att.needs_review > 0 && _jsx(AttentionRow, { to: "/downloads?tab=review", count: att.needs_review, label: "Videos need a match review", tone: "warn" }, "r"),
        att.wanted > 0 && _jsx(AttentionRow, { to: "/downloads?tab=wanted", count: att.wanted, label: "Played games with no video yet", tone: "warn" }, "w"),
    ].filter(Boolean) : [];
    return (_jsxs(Page, { children: [_jsx(PageHeader, { title: "Overview", description: data ? healthLine(data) : _jsx(Skeleton, { className: "h-4 w-64" }) }), _jsx(DownloadingNow, {}), _jsx(Section, { title: "Sync", aside: _jsx(RangeToggle, { value: hours, onChange: setHours }), children: isLoading || !data ? (_jsx("div", { className: "space-y-3 py-3", children: [0, 1].map((i) => _jsx(Skeleton, { className: "h-5 w-full" }, i)) })) : data.subscriptions.length ? (_jsxs(_Fragment, { children: [_jsx(SyncPulse, { subs: data.subscriptions }), _jsxs("div", { className: "flex items-center justify-between gap-4 border-t border-border py-2.5", children: [_jsx(PulseLegend, {}), _jsx("span", { className: "whitespace-nowrap text-[12px] text-muted-foreground", children: hours === 24 ? 'Last 24 hours' : 'Last 7 days' })] })] })) : (_jsxs("p", { className: "py-6 text-[13px] text-muted-foreground", children: ["No subscriptions yet. ", _jsx(Link, { to: "/subscriptions", className: "font-medium text-brand hover:underline", children: "Add one" }), " to start syncing a channel."] })) }), _jsxs("div", { className: "mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_320px]", children: [_jsx(Section, { title: "Recent arrivals", aside: _jsx(Link, { to: "/downloads?tab=history", className: "text-[12px] font-medium text-brand hover:underline", children: "History" }), children: isLoading || !data ? (_jsx("div", { className: "space-y-3 py-3", children: [0, 1, 2, 3].map((i) => _jsx(Skeleton, { className: "h-9 w-full" }, i)) })) : data.recent.length ? (_jsx("ul", { className: "py-1.5", children: data.recent.map((a) => _jsx(ArrivalRow, { a: a }, a.id)) })) : (_jsx("p", { className: "py-6 text-[13px] text-muted-foreground", children: "Nothing downloaded yet. New videos appear here as they finish." })) }), _jsxs("div", { className: "min-w-0 space-y-4", children: [_jsx(Section, { title: "Needs attention", children: attention.length ? _jsx("ul", { className: "py-1.5", children: attention }) : (_jsx("p", { className: "py-4 text-[13px] text-muted-foreground", children: data ? 'Nothing needs you right now.' : '' })) }), data && (_jsxs("dl", { className: "grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border text-[13px]", children: [_jsx(StatTile, { label: "Downloaded, 24h", value: data.last_24h.downloaded, data: data.last_24h.series, dataKey: "count" }), _jsx(StatTile, { label: "Added, 24h", value: formatBytes(data.last_24h.bytes), data: data.last_24h.series, dataKey: "bytes", format: formatBytes })] }))] })] })] }));
}
