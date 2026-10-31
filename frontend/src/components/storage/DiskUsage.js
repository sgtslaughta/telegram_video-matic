import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { formatBytes } from '@/lib/format';
import { cn } from '@/lib/utils';
export function DiskUsage({ s }) {
    const pct = Math.min(100, Math.max(0, s.disk.pct));
    const tone = pct > 90 ? 'bg-err' : pct > 80 ? 'bg-warn' : 'bg-brand';
    return (_jsxs("section", { className: "rounded-lg border border-border bg-card p-4", children: [_jsxs("div", { className: "flex flex-wrap items-baseline justify-between gap-2", children: [_jsxs("p", { className: "text-[13px]", children: [_jsxs("span", { className: "text-[20px] font-semibold tracking-tight", children: [Math.round(pct), "%"] }), ' ', _jsxs("span", { className: "text-muted-foreground", children: [formatBytes(s.disk.used), " of ", formatBytes(s.disk.total), " used"] })] }), _jsx("code", { className: "truncate font-mono text-[12px] text-muted-foreground", title: s.media_root, children: s.media_root })] }), _jsx("div", { role: "progressbar", "aria-label": "Disk usage", "aria-valuenow": Math.round(pct), "aria-valuemin": 0, "aria-valuemax": 100, className: "mt-3 h-2 overflow-hidden rounded-full bg-muted", children: _jsx("div", { className: cn('h-full rounded-full transition-colors', tone), style: { width: `${pct}%` } }) })] }));
}
