import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { absTime, formatBytes, relTime } from '@/lib/format';
import { withToast } from '@/lib/toast';
import { post, dq } from './data';
import { Bar, Empty } from './rows';
export function SearchDialog({ game, onClose }) {
    return (_jsx(Dialog, { open: !!game, onOpenChange: (o) => !o && onClose(), children: _jsx(DialogContent, { className: "max-w-3xl", children: game && _jsx(Body, { game: game }, game.fixture_id) }) }));
}
function Body({ game }) {
    const qc = useQueryClient();
    const [rows, setRows] = useState(null);
    const [error, setError] = useState(null);
    const [grabbed, setGrabbed] = useState(new Set());
    useEffect(() => {
        let live = true;
        post(`/plugins/rugby/wanted/${game.fixture_id}/search?subscription_id=${game.subscription_id}`)
            .then((r) => live && setRows(r))
            .catch((e) => live && setError(e.status === 503 ? 'Telegram is not connected' : e.message))
            .finally(() => qc.invalidateQueries({ queryKey: dq.wanted }));
        return () => { live = false; };
    }, [game, qc]);
    const grab = (c) => withToast(async () => {
        await post(`/plugins/rugby/wanted/${game.fixture_id}/grab`, { channel_id: c.channel_id, tg_msg_id: c.tg_msg_id });
        setGrabbed((s) => new Set(s).add(`${c.channel_id}:${c.tg_msg_id}`));
        qc.invalidateQueries({ queryKey: ['downloads'] });
    }, { success: 'Download queued' });
    return (_jsxs(_Fragment, { children: [_jsxs(DialogHeader, { children: [_jsxs(DialogTitle, { children: [game.home, " vs ", game.away] }), _jsx(DialogDescription, { children: "Matching videos found in your channels. Grab the one you want." })] }), _jsx("div", { className: "max-h-[60vh] overflow-y-auto rounded-md border border-border", children: error ? _jsx(Empty, { children: error })
                    : rows === null ? _jsx("div", { className: "space-y-2 p-3", children: [0, 1, 2].map((i) => _jsx(Skeleton, { className: "h-8 w-full" }, i)) })
                        : rows.length === 0 ? _jsx(Empty, { children: "No matching videos found. The search repeats automatically." })
                            : (_jsxs("table", { className: "w-full text-[13px]", children: [_jsx("thead", { className: "text-left text-[12px] text-muted-foreground", children: _jsxs("tr", { className: "border-b border-border", children: [_jsx("th", { className: "px-3 py-2 font-normal", children: "File" }), _jsx("th", { className: "hidden w-32 px-3 py-2 font-normal sm:table-cell", children: "Match" }), _jsx("th", { className: "hidden px-3 py-2 text-right font-normal sm:table-cell", children: "Size" }), _jsx("th", { className: "hidden px-3 py-2 font-normal md:table-cell", children: "Posted" }), _jsx("th", { className: "w-20" })] }) }), _jsx("tbody", { children: rows.map((c) => {
                                            const key = `${c.channel_id}:${c.tg_msg_id}`;
                                            const done = grabbed.has(key) || c.already_tracked;
                                            return (_jsxs("tr", { className: "h-10 border-b border-border last:border-0 hover:bg-accent/60", children: [_jsxs("td", { className: "max-w-0 px-3", children: [_jsx("p", { className: "truncate", title: c.file_name ?? c.caption ?? undefined, children: c.file_name || c.caption || `Message ${c.tg_msg_id}` }), c.auto && _jsx("p", { className: "text-[12px] text-muted-foreground", children: "Auto-grab candidate" })] }), _jsx("td", { className: "hidden px-3 sm:table-cell", children: _jsx(Bar, { value: c.confidence }) }), _jsx("td", { className: "hidden px-3 text-right tabular-nums text-muted-foreground sm:table-cell", children: formatBytes(c.size_bytes) }), _jsx("td", { className: "hidden whitespace-nowrap px-3 text-muted-foreground md:table-cell", title: absTime(c.date), children: relTime(c.date) }), _jsx("td", { className: "px-3 text-right", children: _jsx(Button, { size: "sm", variant: done ? 'ghost' : 'outline', className: "h-7 px-2 text-[12px]", disabled: done, onClick: () => grab(c), children: done ? 'Queued' : 'Grab' }) })] }, key));
                                        }) })] })) })] }));
}
