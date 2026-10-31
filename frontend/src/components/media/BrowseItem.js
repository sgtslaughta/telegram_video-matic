import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Download, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MediaThumb } from '@/components/shared/MediaThumb';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { RugbyTag } from '@/components/shared/RugbyTag';
import { RugbyMatchup } from '@/components/shared/RugbyMatchup';
import { useItemDownload } from './useItemDownload';
import { formatBytes } from '@/lib/format';
import * as api from '@/lib/api';
const title = (i) => i.caption || i.file_name || 'Untitled';
const ring = (a) => (a ? 'ring-2 ring-brand/60' : '');
function DownloadButton({ item, channelId }) {
    const { onDownload, pending } = useItemDownload(item, channelId);
    return (_jsx(Button, { size: "icon", variant: "ghost", className: "h-8 w-8", "aria-label": "Download", title: "Download", disabled: pending || item.status === 'downloaded', onClick: (e) => { e.stopPropagation(); void onDownload(); }, children: _jsx(Download, { className: "h-4 w-4" }) }));
}
export function BrowseCard({ item, channelId, rugby, index, active, onOpen }) {
    return (_jsxs("article", { "data-nav": index, role: "button", tabIndex: 0, onClick: () => onOpen(item), onKeyDown: (e) => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            onOpen(item);
        } }, className: `flex cursor-pointer flex-col overflow-hidden rounded-lg border bg-card transition-colors hover:bg-accent/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring ${ring(active)}`, children: [_jsx("div", { className: "aspect-video w-full overflow-hidden bg-muted", children: _jsx(MediaThumb, { src: api.channels.browseThumbUrl(channelId, item.tg_msg_id), alt: "", size: "lg", className: "!h-full !w-full !rounded-none" }) }), _jsxs("div", { className: "flex flex-1 flex-col gap-1.5 p-3", children: [rugby ? (_jsxs(_Fragment, { children: [_jsx(RugbyMatchup, { rugby: rugby, size: "sm" }), _jsxs("div", { className: "flex flex-wrap items-center justify-center gap-1.5 text-[11px] text-muted-foreground", children: [rugby.round && _jsxs("span", { className: "rounded bg-brand/10 px-1.5 text-brand", children: ["R", rugby.round] }), rugby.venue && _jsxs("span", { className: "inline-flex items-center gap-0.5", children: [_jsx(MapPin, { className: "h-3 w-3" }), rugby.venue] })] })] })) : (_jsx("p", { className: "line-clamp-2 text-[13px]", children: title(item) })), item.subscription_label && _jsx("p", { className: "truncate text-[12px] text-muted-foreground", children: item.subscription_label }), _jsxs("div", { className: "mt-auto flex items-center gap-2 pt-1", children: [_jsx(StatusBadge, { status: item.status }), _jsx("span", { className: "text-[12px] text-muted-foreground", children: item.size_bytes ? formatBytes(item.size_bytes) : '' }), _jsx("span", { className: "ml-auto", children: _jsx(DownloadButton, { item: item, channelId: channelId }) })] })] })] }));
}
export function BrowseRow({ item, channelId, rugby, index, active, onOpen }) {
    return (_jsxs("div", { "data-nav": index, className: `flex min-h-14 items-center gap-3 px-3 py-2 transition-colors hover:bg-accent/60 ${ring(active)}`, children: [_jsx("button", { onClick: () => onOpen(item), className: "h-10 w-[72px] shrink-0 overflow-hidden rounded-md bg-muted", "aria-label": `Open ${title(item)}`, children: _jsx(MediaThumb, { src: api.channels.browseThumbUrl(channelId, item.tg_msg_id), alt: "", size: "sm", className: "!h-full !w-full" }) }), _jsxs("button", { onClick: () => onOpen(item), className: "min-w-0 flex-1 text-left", children: [_jsx("p", { className: "truncate text-[13px] hover:underline", children: title(item) }), _jsxs("p", { className: "flex items-center gap-1 truncate text-[12px] text-muted-foreground", children: [_jsx("span", { className: "shrink-0", children: new Date(item.date_posted).toLocaleDateString() }), item.subscription_label && _jsxs("span", { className: "shrink-0", children: ["\u00B7 ", item.subscription_label] }), rugby && _jsx(RugbyTag, { rugby: rugby, className: "min-w-0" })] })] }), _jsx("span", { className: "hidden w-20 text-right text-[12px] text-muted-foreground sm:inline", children: item.size_bytes ? formatBytes(item.size_bytes) : '' }), _jsx(StatusBadge, { status: item.status }), _jsx(DownloadButton, { item: item, channelId: channelId })] }));
}
export function BrowseSkeleton({ view }) {
    const n = 8;
    return view === 'cards' ? (_jsx("div", { className: "grid grid-cols-1 gap-3 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4", "aria-busy": "true", children: Array.from({ length: n }, (_, i) => (_jsxs("div", { className: "overflow-hidden rounded-lg border bg-card", children: [_jsx("div", { className: "aspect-video animate-pulse bg-muted" }), _jsxs("div", { className: "space-y-2 p-3", children: [_jsx("div", { className: "h-3.5 w-4/5 animate-pulse rounded bg-muted" }), _jsx("div", { className: "h-3 w-1/2 animate-pulse rounded bg-muted" })] })] }, i))) })) : (_jsx("div", { className: "divide-y rounded-lg border bg-card", "aria-busy": "true", children: Array.from({ length: n }, (_, i) => (_jsxs("div", { className: "flex h-14 items-center gap-3 px-3", children: [_jsx("div", { className: "h-10 w-[72px] animate-pulse rounded-md bg-muted" }), _jsx("div", { className: "h-3.5 w-1/2 animate-pulse rounded bg-muted" })] }, i))) }));
}
