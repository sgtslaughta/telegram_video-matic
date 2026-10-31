import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { GripVertical } from 'lucide-react';
import { downloadKeys } from '@/hooks/useDownloads';
import { fetchAPI } from '@/lib/api';
import { formatBytes } from '@/lib/format';
import { withToast } from '@/lib/toast';
import { cn } from '@/lib/utils';
import { Dot } from './rows';
import { moveItem } from './data';
/** Waiting downloads, reorderable by drag or Alt+↑/↓. First row downloads first. */
export function QueuedRows({ items, grid }) {
    const qc = useQueryClient();
    const nav = useNavigate();
    const [drag, setDrag] = useState(null);
    const [over, setOver] = useState(null);
    const commit = (next) => {
        const prev = items;
        qc.setQueryData(downloadKeys.queued(), next);
        const save = (list) => fetchAPI('/downloads/reorder', { method: 'POST', body: JSON.stringify({ media_ids: list.map((w) => w.media_id) }) });
        void withToast(() => save(next), {
            success: 'Queue order saved',
            undo: async () => {
                qc.setQueryData(downloadKeys.queued(), prev);
                await save(prev);
            },
        });
    };
    const onKey = (e, i, id) => {
        if (e.target !== e.currentTarget)
            return;
        if (e.key === 'Enter')
            nav(`/media/${id}`);
        if (e.altKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
            e.preventDefault();
            const to = e.key === 'ArrowUp' ? i - 1 : i + 1;
            if (to >= 0 && to < items.length)
                commit(moveItem(items, i, to));
        }
    };
    return (_jsx(_Fragment, { children: items.map((q, i) => (_jsxs("div", { role: "row", "data-row": true, tabIndex: 0, draggable: true, "aria-label": `${q.file_name || `Media ${q.media_id}`}, position ${i + 1}. Alt plus arrow keys to move.`, onKeyDown: (e) => onKey(e, i, q.media_id), onDragStart: (e) => { setDrag(i); e.dataTransfer.effectAllowed = 'move'; }, onDragOver: (e) => { e.preventDefault(); setOver(i); }, onDragEnd: () => { setDrag(null); setOver(null); }, onDrop: (e) => {
                e.preventDefault();
                if (drag !== null && drag !== i)
                    commit(moveItem(items, drag, i));
                setDrag(null);
                setOver(null);
            }, className: cn('grid h-10 items-center gap-x-3 border-t border-border px-4 text-[13px] outline-none transition-colors hover:bg-accent/60 focus-visible:bg-accent/60 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-brand', drag === i && 'opacity-40', over === i && drag !== null && drag !== i && 'shadow-[inset_0_2px_0_hsl(var(--brand))]', grid), children: [_jsx(GripVertical, { className: "h-4 w-4 cursor-grab text-muted-foreground", "aria-hidden": true }), _jsx("button", { onClick: () => nav(`/media/${q.media_id}`), className: "truncate text-left hover:underline", title: q.file_name ?? undefined, children: q.file_name || `Media #${q.media_id}` }), _jsx("span", { className: "hidden md:block" }), _jsx("span", { className: "hidden md:block" }), _jsx("span", { className: "hidden md:block" }), _jsx("span", { className: "hidden text-right tabular-nums text-muted-foreground md:block", children: formatBytes(q.size_bytes) }), _jsxs("span", { className: "flex items-center gap-1.5 text-muted-foreground", children: [_jsx(Dot, { tone: "muted" }), "#", i + 1, " in line"] }), _jsx("span", { className: "hidden md:block" })] }, q.media_id))) }));
}
