import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Page } from '@/components/shared/PageHeader';
import { RugbyTag } from '@/components/shared/RugbyTag';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { MediaPlayer } from '@/components/media/MediaPlayer';
import { HistoryTimeline } from '@/components/media/HistoryTimeline';
import { useDownloadMedia, useRequeueMedia } from '@/hooks/useMedia';
import { useActiveDownloads } from '@/hooks/useDownloads';
import { useRugbyEnrichmentByMedia } from '@/hooks/useRugby';
import { useMediaFull, useMediaHistory, useSetKeep } from '@/hooks/useMediaTools';
import { absTime, formatBytes, formatDuration } from '@/lib/format';
import { withToast } from '@/lib/toast';
function Panel({ title, children }) {
    return (_jsxs("section", { className: "rounded-lg border bg-card", children: [_jsx("h2", { className: "flex h-11 items-center border-b px-4 text-[13px] font-semibold", children: title }), children] }));
}
function Loading() {
    return (_jsxs(Page, { children: [_jsx(Skeleton, { className: "mb-4 h-4 w-16" }), _jsx(Skeleton, { className: "aspect-video w-full rounded-lg" }), _jsx(Skeleton, { className: "mt-5 h-7 w-1/2" }), _jsx(Skeleton, { className: "mt-2 h-4 w-2/3" })] }));
}
export default function MediaDetail() {
    const id = parseInt(useParams().id || '0', 10);
    const navigate = useNavigate();
    const qc = useQueryClient();
    const media = useMediaFull(id);
    const history = useMediaHistory(id);
    const downloads = useActiveDownloads();
    const download = useDownloadMedia(id);
    const requeue = useRequeueMedia(id);
    const setKeep = useSetKeep(id);
    const rugby = useRugbyEnrichmentByMedia(id > 0 ? [id] : []).data?.[String(id)];
    if (media.isLoading)
        return _jsx(Loading, {});
    if (media.error || !media.data) {
        return (_jsx(Page, { children: _jsxs("div", { className: "rounded-lg bg-err/10 p-4 text-[13px] text-err", children: ["Could not load this video. ", _jsx(Link, { to: "/browse", className: "underline", children: "Back to browse" })] }) }));
    }
    const item = media.data;
    const live = downloads.data?.find((d) => d.media_id === id);
    const title = rugby ? `${rugby.home} vs ${rugby.away}` : item.caption?.split('\n')[0] || item.file_name || `Video ${id}`;
    const matchDate = item.content_date ?? item.date_posted;
    const reactions = Object.entries((item.reactions ?? {}));
    const refresh = () => {
        qc.invalidateQueries({ queryKey: ['media'] });
        qc.invalidateQueries({ queryKey: ['events'] });
    };
    const toggleKeep = (keep) => withToast(() => setKeep.mutateAsync(keep), {
        success: keep ? 'Keeping this video forever' : 'Video can be cleaned up again',
        undo: () => setKeep.mutateAsync(!keep),
    });
    const meta = [
        rugby?.league, rugby?.round && `Round ${rugby.round}`,
        matchDate && _jsx("span", { title: absTime(matchDate), children: new Date(matchDate).toLocaleDateString() }, "d"),
        item.size_bytes ? formatBytes(item.size_bytes) : null,
        formatDuration(item.duration_sec),
    ].filter(Boolean);
    return (_jsxs(Page, { children: [_jsxs("button", { onClick: () => (window.history.length > 1 ? navigate(-1) : navigate('/browse')), className: "mb-4 inline-flex items-center gap-1 text-[13px] text-brand hover:underline", children: [_jsx(ChevronLeft, { className: "h-4 w-4" }), "Back"] }), _jsx(MediaPlayer, { item: item, progress: live, busy: download.isPending || requeue.isPending, onDownload: () => withToast(() => download.mutateAsync(), { success: 'Download queued' }).then(refresh), onRetry: () => withToast(() => requeue.mutateAsync(), { success: 'Download queued again' }).then(refresh) }), _jsxs("div", { className: "mt-5 flex flex-wrap items-start justify-between gap-4", children: [_jsxs("div", { className: "min-w-0 flex-1", children: [_jsx("h1", { className: "break-words text-[20px] font-semibold leading-7 tracking-tight", children: title }), _jsxs("div", { className: "mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] text-muted-foreground", children: [_jsx(StatusBadge, { status: item.status }), meta.map((m, i) => _jsxs("span", { className: "flex items-center gap-2", children: [i > 0 && _jsx("span", { "aria-hidden": true, children: "\u00B7" }), m] }, i))] }), rugby && _jsx(RugbyTag, { rugby: rugby, className: "mt-2 text-[12px] text-muted-foreground" })] }), _jsxs("label", { className: "flex items-center gap-2 text-[13px]", children: [_jsx(Switch, { checked: !!item.keep, onCheckedChange: toggleKeep, disabled: setKeep.isPending, "aria-label": "Keep forever" }), "Keep forever"] })] }), _jsxs("div", { className: "mt-5 grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]", children: [_jsxs("div", { className: "space-y-4", children: [item.caption && (_jsx(Panel, { title: "Caption", children: _jsx("p", { className: "whitespace-pre-wrap p-4 text-[13px]", children: item.caption }) })), _jsx(Panel, { title: "Details", children: _jsxs("dl", { className: "grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 p-4 text-[13px]", children: [item.file_name && (_jsxs(_Fragment, { children: [_jsx("dt", { className: "text-muted-foreground", children: "File" }), _jsx("dd", { className: "break-all", children: item.file_name })] })), item.local_path && (_jsxs(_Fragment, { children: [_jsx("dt", { className: "text-muted-foreground", children: "Saved to" }), _jsx("dd", { className: "break-all", children: item.local_path })] })), item.mime && (_jsxs(_Fragment, { children: [_jsx("dt", { className: "text-muted-foreground", children: "Type" }), _jsx("dd", { children: item.mime })] })), _jsx("dt", { className: "text-muted-foreground", children: "Posted" }), _jsx("dd", { title: absTime(item.date_posted), children: new Date(item.date_posted).toLocaleDateString() }), reactions.length > 0 && (_jsxs(_Fragment, { children: [_jsx("dt", { className: "text-muted-foreground", children: "Reactions" }), _jsx("dd", { className: "flex flex-wrap gap-1.5", children: reactions.map(([e, n]) => _jsxs("span", { className: "rounded-full bg-muted px-2 text-[12px]", children: [e, " ", n] }, e)) })] })), !!item.comments_count && (_jsxs(_Fragment, { children: [_jsx("dt", { className: "text-muted-foreground", children: "Comments" }), _jsx("dd", { children: item.comments_count })] }))] }) })] }), _jsx(Panel, { title: "History", children: _jsx(HistoryTimeline, { entries: history.data, loading: history.isLoading }) })] })] }));
}
