import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { absTime, formatBytes, relTime } from '@/lib/format';
import { withToast } from '@/lib/toast';
import { cn } from '@/lib/utils';
import { dq, post, useFailed, useWanted } from './data';
import { SearchDialog } from './SearchDialog';
import { Dot, Empty, Row, RowSkeleton, Section } from './rows';
import { useRowNav } from '@/hooks/useRowNav';
const STATE = { missing: ['Missing', 'warn'], searching: ['Searching', 'warn'], not_found: ['Not found', 'muted'] };
function GameRow({ g, onSearch, onDismiss }) {
    const [label, tone] = STATE[g.state] ?? STATE.missing;
    return (_jsxs(Row, { className: "min-h-11 grid-cols-[minmax(0,1fr)_auto] py-1.5 md:grid-cols-[minmax(0,1fr)_minmax(0,200px)_110px_110px_150px]", children: [_jsxs("div", { className: "min-w-0", children: [_jsxs("p", { className: "truncate font-medium", children: [g.home, " vs ", g.away] }), _jsxs("p", { className: "truncate text-[12px] text-muted-foreground md:hidden", children: [g.league, g.round ? `, round ${g.round}` : '', ", ", relTime(g.date)] })] }), _jsxs("p", { className: "hidden truncate text-muted-foreground md:block", children: [g.league, g.round ? `, round ${g.round}` : ''] }), _jsx("span", { className: "hidden text-muted-foreground md:block", title: absTime(g.date), children: relTime(g.date) }), _jsxs("span", { className: cn('hidden items-center gap-1.5 md:flex', g.state === 'not_found' && 'text-muted-foreground'), children: [_jsx(Dot, { tone: tone }), label] }), _jsxs("div", { className: "flex justify-end gap-1", children: [_jsx(Button, { size: "sm", variant: "outline", className: "h-7 px-2 text-[12px]", onClick: onSearch, children: "Search" }), _jsx(Button, { size: "sm", variant: "ghost", className: "h-7 px-2 text-[12px]", onClick: onDismiss, children: "Dismiss" })] })] }));
}
export function WantedTab() {
    const qc = useQueryClient();
    const wanted = useWanted();
    const failed = useFailed();
    const [target, setTarget] = useState(null);
    const [sel, setSel] = useState(new Set());
    const ref = useRowNav();
    const games = wanted.data;
    const fails = failed.data ?? [];
    const dismiss = (g) => withToast(async () => {
        await post(`/plugins/rugby/wanted/${g.fixture_id}/dismiss?subscription_id=${g.subscription_id}`);
        qc.invalidateQueries({ queryKey: dq.wanted });
    }, { success: `Dismissed ${g.home} vs ${g.away}` });
    const retry = (ids) => withToast(async () => {
        await Promise.all(ids.map((id) => post(`/media/${id}/requeue`)));
        setSel(new Set());
        qc.invalidateQueries({ queryKey: ['downloads'] });
    }, { success: `Retried ${ids.length} download${ids.length === 1 ? '' : 's'}` });
    const toggle = (id) => setSel((s) => { const n = new Set(s); if (!n.delete(id))
        n.add(id); return n; });
    const ids = sel.size ? [...sel] : fails.map((f) => f.media_id);
    return (_jsxs("div", { ref: ref, children: [games !== null && (_jsx(Section, { title: "Missing games", aside: games && _jsx("span", { className: "text-[12px] text-muted-foreground", children: games.length }), children: wanted.isLoading ? _jsx(RowSkeleton, {})
                    : !games?.length ? _jsx(Empty, { children: "No missing games. Played fixtures without a video show up here." })
                        : games.map((g) => _jsx(GameRow, { g: g, onSearch: () => setTarget(g), onDismiss: () => dismiss(g) }, g.fixture_id)) })), _jsx(Section, { title: "Failed downloads", aside: fails.length > 0 && (_jsx(Button, { size: "sm", variant: "outline", className: "h-7 px-2 text-[12px]", onClick: () => retry(ids), children: sel.size ? `Retry ${sel.size} selected` : 'Retry all' })), children: failed.isLoading ? _jsx(RowSkeleton, {})
                    : !fails.length ? _jsx(Empty, { children: "No failed downloads." })
                        : fails.map((f) => (_jsxs(Row, { to: `/media/${f.media_id}`, selected: sel.has(f.media_id), className: "min-h-11 grid-cols-[20px_minmax(0,1fr)_auto] py-1.5 md:grid-cols-[20px_minmax(0,1fr)_minmax(0,260px)_80px_110px_90px]", children: [_jsx(Checkbox, { "aria-label": "Select failed download", className: "rounded", checked: sel.has(f.media_id), onCheckedChange: () => toggle(f.media_id) }), _jsxs("div", { className: "min-w-0", children: [_jsx(Link, { to: `/media/${f.media_id}`, className: "block truncate font-medium hover:underline", children: f.file_name || f.caption || `Media #${f.media_id}` }), _jsx("p", { className: "truncate text-[12px] text-err md:hidden", children: f.error })] }), _jsx("p", { className: "hidden truncate text-[12px] text-err md:block", title: f.error ?? undefined, children: f.error }), _jsx("span", { className: "hidden text-right tabular-nums text-muted-foreground md:block", children: formatBytes(f.size_bytes) }), _jsx("span", { className: "hidden text-muted-foreground md:block", title: absTime(f.last_attempt_at), children: relTime(f.last_attempt_at) }), _jsx("div", { className: "flex justify-end", children: _jsx(Button, { size: "sm", variant: "ghost", className: "h-7 px-2 text-[12px]", onClick: () => retry([f.media_id]), children: "Retry download" }) })] }, f.media_id))) }), _jsx(SearchDialog, { game: target, onClose: () => setTarget(null) })] }));
}
