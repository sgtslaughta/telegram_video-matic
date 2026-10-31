import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Play } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Thumb } from '@/components/shared/Thumb';
import { useSummary, markSeen } from '@/hooks/useSummary';
import { absTime, formatBytes, relTime } from '@/lib/format';
function incidentText(i) {
    const span = i.hours >= 48 ? `${Math.round(i.hours / 24)} days` : `${i.hours} hour${i.hours === 1 ? '' : 's'}`;
    return i.ended
        ? `Telegram was offline for about ${span}, from ${absTime(i.started)}. Sync recovered on its own.`
        : `Telegram has been offline for about ${span}. Sync resumes once it reconnects.`;
}
/** "Since your last visit" — shown once when you return after 6h+ and something happened. */
export default function WelcomeSplash() {
    const { data } = useSummary();
    const [dismissed, setDismissed] = useState(false);
    const open = !!data?.show && !dismissed;
    // Nothing to show: still record the visit (no state change, so no re-render loop).
    useEffect(() => {
        if (data && !data.show)
            void markSeen().catch(() => { });
    }, [data]);
    const close = (o) => {
        if (o)
            return;
        setDismissed(true);
        void markSeen().catch(() => { });
    };
    if (!data?.show)
        return null;
    const a = data.attention;
    const needs = [
        a.failed > 0 && { to: '/downloads?tab=wanted', label: `${a.failed} failed download${a.failed === 1 ? '' : 's'}` },
        a.cleanup_paused && { to: '/storage', label: `Cleanup waiting for approval (${a.cleanup_paused.count} files)` },
        a.needs_review > 0 && { to: '/downloads?tab=review', label: `${a.needs_review} video${a.needs_review === 1 ? '' : 's'} to review` },
        a.wanted > 0 && { to: '/downloads?tab=wanted', label: `${a.wanted} played game${a.wanted === 1 ? '' : 's'} with no video yet` },
    ].filter(Boolean);
    return (_jsx(Dialog, { open: open, onOpenChange: close, children: _jsxs(DialogContent, { className: "max-h-[85vh] gap-0 overflow-y-auto p-0 sm:max-w-2xl", children: [_jsxs("div", { className: "border-b border-border px-6 py-5", children: [_jsx(DialogTitle, { className: "text-[20px] font-semibold tracking-tight", children: "Since your last visit" }), _jsx(DialogDescription, { className: "mt-1 text-[13px]", title: absTime(data.since), children: data.stats.downloaded
                                ? `${data.stats.downloaded} new video${data.stats.downloaded === 1 ? '' : 's'}, ${formatBytes(data.stats.bytes)} added since ${relTime(data.since)}.`
                                : `Here’s what happened since ${relTime(data.since)}.` })] }), data.incidents.length > 0 && (_jsx("div", { className: "space-y-2 border-b border-border bg-err/5 px-6 py-4", children: data.incidents.map((i) => (_jsxs("p", { className: "flex gap-2.5 text-[13px]", children: [_jsx(AlertTriangle, { className: "mt-0.5 h-4 w-4 shrink-0 text-err" }), incidentText(i)] }, i.started))) })), data.arrivals.map((g) => (_jsxs("section", { className: "border-b border-border px-6 py-4", children: [_jsx("h3", { className: "mb-3 text-[13px] font-semibold", children: g.group }), _jsx("ul", { className: "grid grid-cols-2 gap-3 sm:grid-cols-3", children: g.items.slice(0, 6).map((it) => (_jsx("li", { children: _jsxs(Link, { to: `/media/${it.id}`, onClick: () => close(false), className: "group block", children: [_jsxs("div", { className: "relative flex aspect-video items-center justify-center overflow-hidden rounded-md bg-muted", children: [_jsx(Thumb, { id: it.id, className: "absolute inset-0 rounded-none" }), _jsx("span", { className: "absolute flex h-8 w-8 items-center justify-center rounded-full bg-brand text-primary-foreground opacity-90 transition-transform group-hover:scale-105", children: _jsx(Play, { className: "ml-0.5 h-4 w-4", fill: "currentColor" }) })] }), _jsx("p", { className: "mt-1.5 truncate text-[12px] font-medium", children: it.title })] }) }, it.id))) }), g.items.length > 6 && _jsxs("p", { className: "mt-2 text-[12px] text-muted-foreground", children: ["and ", g.items.length - 6, " more"] })] }, g.group))), needs.length > 0 && (_jsxs("section", { className: "border-b border-border px-6 py-4", children: [_jsx("h3", { className: "mb-2 text-[13px] font-semibold", children: "Needs attention" }), _jsx("ul", { className: "space-y-1", children: needs.map((n) => (_jsx("li", { children: _jsx(Link, { to: n.to, onClick: () => close(false), className: "text-[13px] text-brand hover:underline", children: n.label }) }, n.label))) })] })), _jsx("div", { className: "flex justify-end px-6 py-4", children: _jsx(Button, { onClick: () => close(false), children: "Done" }) })] }) }));
}
