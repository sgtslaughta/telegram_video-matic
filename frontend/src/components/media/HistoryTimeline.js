import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Skeleton } from '@/components/ui/skeleton';
import { absTime, relTime } from '@/lib/format';
const DOT = { info: 'bg-muted-foreground/50', success: 'bg-ok', warning: 'bg-warn', error: 'bg-err' };
export function HistoryTimeline({ entries, loading }) {
    if (loading) {
        return _jsx("div", { className: "space-y-3 p-4", "aria-busy": "true", children: [0, 1, 2].map((i) => _jsx(Skeleton, { className: "h-4 w-3/4" }, i)) });
    }
    if (!entries?.length)
        return _jsx("p", { className: "p-4 text-[13px] text-muted-foreground", children: "No history yet. Events for this video will show up here." });
    return (_jsx("ol", { className: "p-4", children: entries.map((h, i) => (_jsxs("li", { className: "relative flex gap-3 pb-4 last:pb-0", children: [i < entries.length - 1 && _jsx("span", { className: "absolute left-[3px] top-3 h-full w-px bg-border" }), _jsx("span", { className: `relative mt-1.5 h-2 w-2 shrink-0 rounded-full ${DOT[h.level] ?? DOT.info}` }), _jsxs("div", { className: "min-w-0 flex-1", children: [_jsx("p", { className: "break-words text-[13px]", children: h.message }), _jsxs("p", { className: "text-[12px] text-muted-foreground", children: [_jsx("span", { children: h.kind }), " \u00B7 ", _jsx("span", { title: absTime(h.at), children: relTime(h.at) })] })] })] }, `${h.at}-${i}`))) }));
}
