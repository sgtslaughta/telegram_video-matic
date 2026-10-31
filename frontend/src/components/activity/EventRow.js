import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import { absTime, relTime } from '@/lib/format';
const DOT = {
    info: 'bg-muted-foreground/50', success: 'bg-ok', warning: 'bg-warn', error: 'bg-err',
};
export function EventRow({ e, index, active, onHover }) {
    const when = e.updated_at ?? e.created_at;
    const n = e.count ?? 1;
    const link = e.media_id ? `/media/${e.media_id}` : e.subscription_id ? `/subscriptions/${e.subscription_id}` : null;
    return (_jsxs("li", { "data-nav": index, onMouseEnter: () => onHover(index), className: `flex min-h-10 items-center gap-3 px-4 py-2 transition-colors ${active ? 'bg-accent/60' : ''}`, children: [_jsx("span", { className: `h-2 w-2 shrink-0 rounded-full ${DOT[e.level] ?? DOT.info}`, role: "img", "aria-label": e.level }), _jsxs("div", { className: "flex min-w-0 flex-1 flex-wrap items-center gap-x-2 gap-y-0.5", children: [link ? (_jsx(Link, { to: link, className: "min-w-0 break-words text-[13px] hover:underline", children: e.message })) : (_jsx("span", { className: "min-w-0 break-words text-[13px]", children: e.message })), n > 1 && (_jsxs("span", { className: "rounded-full bg-muted px-1.5 text-[11px] font-medium text-muted-foreground", title: `Repeated ${n} times, last ${relTime(when)}`, children: ["\u00D7", n] }))] }), _jsx("span", { className: "hidden rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground sm:inline", children: e.kind }), _jsx("span", { className: "w-20 shrink-0 text-right text-[12px] text-muted-foreground", title: absTime(when), children: relTime(when) })] }));
}
