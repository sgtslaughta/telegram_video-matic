import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useInfiniteQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Ban, CheckCircle2, CircleDot, Link2, Trash2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { fetchAPI } from '@/lib/api';
import { absTime, relTime } from '@/lib/format';
import { cn } from '@/lib/utils';
import { dq } from './data';
import { Empty, Row, RowSkeleton, Section } from './rows';
import { useRowNav } from '@/hooks/useRowNav';
const PAGE = 50;
const KINDS = [['', 'All'], ['downloaded', 'Downloaded'], ['failed', 'Failed'], ['skipped', 'Skipped'], ['deleted', 'Deleted'], ['matched', 'Matched']];
const ICON = {
    downloaded: [CheckCircle2, 'text-ok'], failed: [XCircle, 'text-err'], skipped: [Ban, 'text-muted-foreground'],
    deleted: [Trash2, 'text-muted-foreground'], matched: [Link2, 'text-brand'], other: [CircleDot, 'text-muted-foreground'],
};
export function HistoryTab({ kind, setKind }) {
    const q = useInfiniteQuery({
        queryKey: [...dq.history, kind],
        initialPageParam: 0,
        queryFn: ({ pageParam }) => fetchAPI('/history', { params: { limit: PAGE, offset: pageParam, kind } }),
        getNextPageParam: (last, all) => (last.length < PAGE ? undefined : all.length * PAGE),
    });
    const ref = useRowNav();
    const items = q.data?.pages.flat() ?? [];
    const chips = (_jsx("div", { role: "radiogroup", "aria-label": "Filter by type", className: "flex flex-wrap gap-1 text-[12px]", children: KINDS.map(([k, l]) => (_jsx("button", { role: "radio", "aria-checked": kind === k, onClick: () => setKind(k), className: cn('rounded-md border px-2 py-0.5 transition-colors', kind === k ? 'border-brand/30 bg-brand/10 font-medium text-brand' : 'border-border text-muted-foreground hover:text-foreground'), children: l }, k))) }));
    return (_jsx("div", { ref: ref, children: _jsxs(Section, { title: "History", aside: _jsx("div", { className: "hidden sm:block", children: chips }), children: [_jsx("div", { className: "border-b border-border px-4 py-2 sm:hidden", children: chips }), q.isLoading ? _jsx(RowSkeleton, { n: 6 })
                    : !items.length ? _jsx(Empty, { children: "No history yet. Downloads, failures and skipped videos are recorded here." })
                        : items.map((h, i) => {
                            const [Icon, tone] = ICON[h.kind] ?? ICON.other;
                            return (_jsxs(Row, { to: h.media_id ? `/media/${h.media_id}` : undefined, className: "min-h-10 grid-cols-[16px_minmax(0,1fr)_auto] py-1.5", children: [_jsx(Icon, { className: cn('h-4 w-4', tone), strokeWidth: 1.75, "aria-label": h.kind }), _jsxs("div", { className: "min-w-0", children: [h.media_id
                                                ? _jsx(Link, { to: `/media/${h.media_id}`, className: "block truncate font-medium hover:underline", children: h.file_name || h.message })
                                                : _jsx("p", { className: "truncate font-medium", children: h.file_name || h.message }), h.file_name && _jsx("p", { className: "truncate text-[12px] text-muted-foreground", children: h.message })] }), _jsx("span", { className: "whitespace-nowrap text-[12px] text-muted-foreground", title: absTime(h.at), children: relTime(h.at) })] }, `${h.at}-${i}`));
                        }), q.hasNextPage && (_jsx("div", { className: "border-t border-border p-2 text-center", children: _jsx(Button, { variant: "ghost", size: "sm", disabled: q.isFetchingNextPage, onClick: () => q.fetchNextPage(), children: "Load more" }) }))] }) }));
}
