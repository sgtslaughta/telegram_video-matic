import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AlertTriangle, Ban, Download, Loader2, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ProgressBar } from '@/components/shared/ProgressBar';
import { formatBytes } from '@/lib/format';
const frame = 'aspect-video w-full overflow-hidden rounded-lg border bg-black';
export function MediaPlayer({ item, progress, busy, onDownload, onRetry }) {
    if (item.status === 'downloaded') {
        return (_jsx("div", { className: frame, children: _jsx("video", { controls: true, preload: "metadata", src: `/api/media/${item.id}/stream`, poster: `/api/media/${item.id}/thumb`, className: "h-full w-full" }) }));
    }
    const failed = item.status === 'failed';
    const skipped = !!item.skip_reason && !failed;
    const loading = item.status === 'downloading' || item.status === 'processing';
    const Icon = failed ? AlertTriangle : skipped ? Ban : loading ? Loader2 : Download;
    const title = failed ? 'Download failed' : skipped ? 'Skipped' : loading ? 'Downloading' : 'Not downloaded yet';
    const body = failed
        ? item.error || 'The download did not finish. Retry to queue it again.'
        : skipped
            ? item.skip_reason
            : loading
                ? 'The video will be playable here when the download finishes.'
                : 'Download this video to watch it here.';
    return (_jsxs("div", { className: `${frame} relative bg-muted`, children: [_jsx("img", { src: `/api/media/${item.id}/thumb`, alt: "", className: "absolute inset-0 h-full w-full object-cover opacity-20 blur-sm", onError: (e) => { e.currentTarget.style.display = 'none'; } }), _jsxs("div", { className: "relative flex h-full flex-col items-center justify-center gap-2 p-6 text-center", children: [_jsx(Icon, { className: `h-6 w-6 ${failed ? 'text-err' : 'text-muted-foreground'} ${loading ? 'animate-spin' : ''}` }), _jsx("p", { className: "text-[13px] font-semibold", children: title }), _jsx("p", { className: "max-w-md text-[13px] text-muted-foreground", children: body }), loading && progress && (_jsxs("div", { className: "w-full max-w-xs space-y-1", children: [_jsx(ProgressBar, { progress: (progress.progress || 0) * 100, animated: true }), !!progress.bytes_total && (_jsxs("p", { className: "text-[12px] text-muted-foreground", children: [formatBytes(progress.bytes_done), " of ", formatBytes(progress.bytes_total)] }))] })), failed && (_jsxs(Button, { size: "sm", onClick: onRetry, disabled: busy, children: [_jsx(RotateCw, { className: "mr-1.5 h-3.5 w-3.5" }), "Retry download"] })), !failed && !loading && (_jsxs(Button, { size: "sm", onClick: onDownload, disabled: busy, children: [_jsx(Download, { className: "mr-1.5 h-3.5 w-3.5" }), "Download"] }))] })] }));
}
