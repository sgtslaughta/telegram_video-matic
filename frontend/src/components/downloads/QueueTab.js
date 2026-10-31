import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Pause, Play, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads';
import { formatBytes } from '@/lib/format';
import { withToast } from '@/lib/toast';
import { post } from './data';
import { Bar, Dot, Empty, Row, RowSkeleton, Section } from './rows';
import { useRowNav } from '@/hooks/useRowNav';
import { QueuedRows } from './QueuedRows';
const GRID = 'grid-cols-[20px_minmax(0,1fr)_auto] md:grid-cols-[20px_minmax(0,1fr)_160px_80px_64px_72px_88px_84px]';
function eta(sec) {
    if (!sec || sec <= 0)
        return '-';
    const m = Math.floor(sec / 60);
    return m ? `${m}m ${Math.floor(sec % 60)}s` : `${Math.floor(sec)}s`;
}
export function QueueTab() {
    const qc = useQueryClient();
    const active = useActiveDownloads();
    const queued = useQueuedDownloads();
    const [sel, setSel] = useState(new Set());
    const ref = useRowNav();
    const jobs = active.data ?? [];
    const waiting = queued.data ?? [];
    const refresh = () => qc.invalidateQueries({ queryKey: ['downloads'] });
    const act = (ids, verb) => {
        const done = { pause: 'Paused', resume: 'Resumed', cancel: 'Canceled' }[verb];
        return withToast(async () => {
            await Promise.all(ids.map((id) => post(`/downloads/${id}/${verb}`)));
            setSel(new Set());
            refresh();
        }, { success: `${done} ${ids.length} download${ids.length === 1 ? '' : 's'}` });
    };
    const toggle = (id) => setSel((s) => { const n = new Set(s); if (!n.delete(id))
        n.add(id); return n; });
    const allSelected = jobs.length > 0 && sel.size === jobs.length;
    const bulk = sel.size > 0 && (_jsxs("div", { className: "flex items-center gap-1", children: [_jsxs("span", { className: "mr-1 text-[12px] text-muted-foreground", children: [sel.size, " selected"] }), _jsx(Button, { size: "sm", variant: "outline", className: "h-7 px-2 text-[12px]", onClick: () => act([...sel], 'pause'), children: "Pause" }), _jsx(Button, { size: "sm", variant: "outline", className: "h-7 px-2 text-[12px]", onClick: () => act([...sel], 'cancel'), children: "Cancel" })] }));
    if (active.isLoading)
        return _jsx(Section, { title: "Queue", children: _jsx(RowSkeleton, {}) });
    if (!jobs.length && !waiting.length) {
        return _jsx(Section, { title: "Queue", children: _jsx(Empty, { children: "Nothing downloading. New videos from your subscriptions queue here automatically." }) });
    }
    return (_jsx("div", { ref: ref, children: _jsx(Section, { title: "Queue", aside: bulk || undefined, children: _jsxs("div", { role: "table", children: [_jsxs("div", { role: "row", className: `hidden h-9 items-center gap-x-3 border-b border-border px-4 text-[12px] text-muted-foreground md:grid ${GRID}`, children: [_jsx(Checkbox, { "aria-label": "Select all", className: "rounded", checked: allSelected, onCheckedChange: () => setSel(allSelected ? new Set() : new Set(jobs.map((j) => j.id))) }), _jsx("span", { children: "Title" }), _jsx("span", { children: "Progress" }), _jsx("span", { className: "text-right", children: "Speed" }), _jsx("span", { className: "text-right", children: "ETA" }), _jsx("span", { className: "text-right", children: "Size" }), _jsx("span", { children: "Status" }), _jsx("span", {})] }), jobs.map((j) => {
                        const paused = j.status === 'paused';
                        return (_jsxs(Row, { to: `/media/${j.media_id}`, selected: sel.has(j.id), className: `min-h-10 py-1.5 ${GRID}`, children: [_jsx(Checkbox, { "aria-label": "Select download", className: "rounded", checked: sel.has(j.id), onCheckedChange: () => toggle(j.id) }), _jsxs("div", { className: "min-w-0", children: [_jsx("p", { className: "truncate font-medium", title: j.file_name ?? undefined, children: j.file_name || `Download #${j.id}` }), j.error && _jsx("p", { className: "truncate text-[12px] text-err", children: j.error }), _jsx("div", { className: "mt-1 md:hidden", children: _jsx(Bar, { value: j.progress ?? 0 }) })] }), _jsx("div", { className: "hidden md:block", children: _jsx(Bar, { value: j.progress ?? 0 }) }), _jsx("span", { className: "hidden text-right tabular-nums text-muted-foreground md:block", children: j.speed_bps ? `${formatBytes(j.speed_bps)}/s` : '-' }), _jsx("span", { className: "hidden text-right tabular-nums text-muted-foreground md:block", children: eta(j.eta_sec) }), _jsx("span", { className: "hidden text-right tabular-nums text-muted-foreground md:block", children: formatBytes(j.bytes_total) }), _jsxs("span", { className: "hidden items-center gap-1.5 md:flex", children: [_jsx(Dot, { tone: paused ? 'muted' : 'warn' }), paused ? 'Paused' : 'Downloading'] }), _jsxs("div", { className: "flex justify-end gap-0.5", children: [_jsx(Button, { size: "icon", variant: "ghost", className: "h-7 w-7", "aria-label": paused ? 'Resume download' : 'Pause download', onClick: () => act([j.id], paused ? 'resume' : 'pause'), children: paused ? _jsx(Play, { className: "h-3.5 w-3.5" }) : _jsx(Pause, { className: "h-3.5 w-3.5" }) }), _jsx(Button, { size: "icon", variant: "ghost", className: "h-7 w-7 hover:text-err", "aria-label": "Cancel download", onClick: () => act([j.id], 'cancel'), children: _jsx(X, { className: "h-3.5 w-3.5" }) })] })] }, j.id));
                    }), _jsx(QueuedRows, { items: waiting, grid: GRID })] }) }) }));
}
