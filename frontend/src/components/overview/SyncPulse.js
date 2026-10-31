import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import { Sparkline } from '@/components/shared/Sparkline';
import { absTime, relTime } from '@/lib/format';
import { outageSpans } from './spans';
function summary(s, spans) {
    const found = s.pulse.reduce((n, c) => n + c.queued, 0);
    const offline = spans.filter((x) => x.kind === 'down').reduce((n, x) => n + x.to - x.from + 1, 0);
    const bits = [`${found} new video${found === 1 ? '' : 's'}`];
    if (offline)
        bits.push(`offline ${offline}h`);
    return bits.join(', ');
}
function Row({ s }) {
    const spans = outageSpans(s.pulse);
    return (_jsxs("div", { className: "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-6 gap-y-2 py-3 md:grid-cols-[minmax(0,200px)_1fr_auto]", children: [_jsxs("div", { className: "min-w-0", children: [_jsx(Link, { to: `/subscriptions/${s.id}`, className: "block truncate text-[13px] font-medium hover:underline", children: s.name }), _jsx("p", { className: "truncate text-[12px] text-muted-foreground", children: s.live ? 'Live' : s.enabled ? summary(s, spans) : 'Paused' })] }), _jsx("div", { role: "img", "aria-label": `${s.name}: ${summary(s, spans)}`, className: "order-last col-span-2 min-w-0 md:order-none md:col-span-1", children: _jsx(Sparkline, { data: s.pulse, dataKey: "queued", label: "New videos", bands: spans.map((x) => ({ from: x.from, to: x.to, tone: x.kind === 'down' ? 'err' : 'warn' })) }) }), _jsx("span", { className: "whitespace-nowrap text-right text-[12px] text-muted-foreground", title: absTime(s.last_checked_at), children: s.enabled ? `Synced ${relTime(s.last_checked_at)}` : '' })] }));
}
export function SyncPulse({ subs }) {
    return _jsx("div", { className: "divide-y divide-border", children: subs.map((s) => _jsx(Row, { s: s }, s.id)) });
}
export function PulseLegend() {
    return (_jsxs("ul", { className: "flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-muted-foreground", children: [_jsxs("li", { className: "flex items-center gap-1.5", children: [_jsx("span", { className: "h-0.5 w-4 rounded bg-brand" }), "New videos per hour"] }), _jsxs("li", { className: "flex items-center gap-1.5", children: [_jsx("span", { className: "h-2.5 w-3 rounded-sm bg-err/20" }), "Telegram offline"] }), _jsxs("li", { className: "flex items-center gap-1.5", children: [_jsx("span", { className: "h-2.5 w-3 rounded-sm bg-warn/20" }), "Failed polls"] })] }));
}
