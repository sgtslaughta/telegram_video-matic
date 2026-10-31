import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { forwardRef } from 'react';
import { MoreHorizontal } from 'lucide-react';
import { Sparkline } from '@/components/shared/Sparkline';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Switch } from '@/components/ui/switch';
import { useUpdateSubscription } from '@/hooks/useSubscriptions';
import { absTime, formatBytes, relTime } from '@/lib/format';
import { withToast } from '@/lib/toast';
import { filterSummary } from './summary';
const FREQ = {
    realtime: 'Real-time', '1m': 'Every minute', '5m': 'Every 5 min', '15m': 'Every 15 min',
    '30m': 'Every 30 min', hourly: 'Hourly', daily: 'Daily', scheduled: 'Weekdays',
};
export const SubscriptionRow = forwardRef(function SubscriptionRow({ sub, title, detail, pulse, focused, onOpen, onFocus, onDelete, onScan }, ref) {
    const update = useUpdateSubscription(sub.id);
    const toggle = (enabled) => withToast(() => update.mutateAsync({ enabled }), {
        success: `${enabled ? 'Enabled' : 'Paused'} ${title}`,
        undo: () => update.mutateAsync({ enabled: !enabled }),
    });
    const stop = (e) => e.stopPropagation();
    const checked = pulse?.last_checked_at ?? null;
    return (_jsxs("tr", { ref: ref, tabIndex: focused ? 0 : -1, "data-sub-id": sub.id, onClick: onOpen, onFocus: onFocus, onKeyDown: (e) => { if (e.key === 'Enter' && e.target === e.currentTarget)
            onOpen(); }, className: "h-12 cursor-pointer border-b border-border outline-none transition-colors last:border-0 hover:bg-accent/60 focus-visible:bg-accent/60 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-brand", children: [_jsx("td", { className: "max-w-[260px] pl-4 pr-3", children: _jsxs("div", { className: "flex items-center gap-2.5", children: [_jsx("span", { role: "img", "aria-label": sub.enabled ? 'Enabled' : 'Paused', className: `h-2 w-2 shrink-0 rounded-full ${sub.enabled ? 'bg-ok' : 'bg-muted-foreground/40'}` }), _jsxs("div", { className: "min-w-0", children: [_jsx("p", { className: "truncate font-medium", children: title }), detail && _jsx("p", { className: "truncate text-[12px] text-muted-foreground", children: detail })] })] }) }), _jsx("td", { className: "hidden whitespace-nowrap px-3 text-muted-foreground md:table-cell", children: FREQ[sub.check_frequency ?? ''] ?? sub.check_frequency ?? '' }), _jsx("td", { className: "hidden max-w-[200px] truncate px-3 text-muted-foreground lg:table-cell", title: sub.filter_regex ?? undefined, children: filterSummary(sub) }), _jsx("td", { className: "hidden whitespace-nowrap px-3 text-right tabular-nums text-muted-foreground lg:table-cell", children: sub.downloaded_count != null ? `${sub.downloaded_count} video${sub.downloaded_count === 1 ? '' : 's'}, ${formatBytes(sub.downloaded_bytes)}` : '' }), _jsx("td", { className: "hidden whitespace-nowrap px-3 text-right text-[12px] text-muted-foreground md:table-cell", title: absTime(checked), children: sub.enabled ? relTime(checked) : '' }), _jsx("td", { className: "hidden w-32 px-3 xl:table-cell", children: pulse && _jsx(Sparkline, { data: pulse.pulse, dataKey: "queued", label: "New videos", className: "h-7" }) }), _jsx("td", { className: "px-3", onClick: stop, children: _jsx(Switch, { checked: sub.enabled, onCheckedChange: toggle, "aria-label": `${sub.enabled ? 'Pause' : 'Enable'} ${title}` }) }), _jsx("td", { className: "w-10 pr-3", onClick: stop, onKeyDown: stop, children: _jsxs(DropdownMenu, { children: [_jsx(DropdownMenuTrigger, { asChild: true, children: _jsx(Button, { variant: "ghost", size: "icon", className: "h-8 w-8", "aria-label": `Actions for ${title}`, children: _jsx(MoreHorizontal, { className: "h-4 w-4" }) }) }), _jsxs(DropdownMenuContent, { align: "end", children: [_jsx(DropdownMenuItem, { onSelect: onOpen, children: "Edit" }), _jsx(DropdownMenuItem, { onSelect: onScan, children: "Scan now" }), _jsx(DropdownMenuItem, { onSelect: onDelete, className: "text-err", children: "Delete" })] })] }) })] }));
});
