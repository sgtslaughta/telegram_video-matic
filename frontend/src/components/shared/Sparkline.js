import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Area, AreaChart, ReferenceArea, XAxis, YAxis } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { cn } from '@/lib/utils';
/** Minimal shadcn area sparkline: no axes, optional shaded bands, hover tooltip. */
export function Sparkline({ data, dataKey, label, bands = [], format, className, labelKey = 't', }) {
    const config = { [dataKey]: { label, color: 'hsl(var(--brand))' } };
    const gid = `spark-${dataKey}`;
    const rows = data.map((d, i) => ({ ...d, i }));
    return (_jsx(ChartContainer, { config: config, className: cn('block aspect-auto h-10 w-full min-w-0', className), children: _jsxs(AreaChart, { data: rows, margin: { top: 4, right: 1, bottom: 0, left: 1 }, children: [_jsx("defs", { children: _jsxs("linearGradient", { id: gid, x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "0%", stopColor: `var(--color-${dataKey})`, stopOpacity: 0.28 }), _jsx("stop", { offset: "100%", stopColor: `var(--color-${dataKey})`, stopOpacity: 0 })] }) }), _jsx(XAxis, { dataKey: "i", type: "number", domain: [0, Math.max(rows.length - 1, 1)], hide: true }), _jsx(YAxis, { hide: true, domain: [0, (max) => Math.max(max, 1) * 1.15] }), bands.map((b) => (_jsx(ReferenceArea, { x1: Math.max(b.from - 0.5, 0), x2: Math.min(b.to + 0.5, rows.length - 1), fill: `hsl(var(--${b.tone}))`, fillOpacity: 0.14, strokeOpacity: 0, ifOverflow: "hidden" }, `${b.from}-${b.tone}`))), _jsx(ChartTooltip, { cursor: { stroke: 'hsl(var(--border))' }, isAnimationActive: false, content: _jsx(ChartTooltipContent, { indicator: "line", labelFormatter: (_, p) => {
                            const t = p?.[0]?.payload?.[labelKey];
                            return t ? new Date(t).toLocaleString(undefined, { weekday: 'short', hour: 'numeric' }) : '';
                        }, formatter: (v) => (_jsxs("span", { className: "flex w-full justify-between gap-3", children: [_jsx("span", { className: "text-muted-foreground", children: label }), _jsx("span", { className: "font-medium tabular-nums", children: format ? format(Number(v)) : String(v) })] })) }) }), _jsx(Area, { type: "monotone", dataKey: dataKey, stroke: `var(--color-${dataKey})`, strokeWidth: 1.5, fill: `url(#${gid})`, isAnimationActive: false, dot: false, activeDot: { r: 3, strokeWidth: 0 } })] }) }));
}
/** Stat tile: label, big tabular number, sparkline underneath. */
export function StatTile({ label, value, data, dataKey, format, }) {
    return (_jsxs("div", { className: "bg-card px-4 pb-2 pt-3", children: [_jsx("dt", { className: "text-[12px] text-muted-foreground", children: label }), _jsx("dd", { className: "mt-0.5 text-[18px] font-semibold tabular-nums", children: value }), _jsx(Sparkline, { data: data, dataKey: dataKey, label: label, format: format, className: "mt-1 h-8" })] }));
}
