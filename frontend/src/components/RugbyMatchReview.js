import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { toast } from 'sonner';
import { useRugbyMatches, useLeagueFixtures, usePatchMatch, useRefreshCatalog } from '@/hooks/useRugby';
import { Skeleton } from '@/components/ui/skeleton';
import { absTime, relTime } from '@/lib/format';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RotateCw } from 'lucide-react';
export function RugbyMatchReview() {
    const { data: matches, isLoading: matchesLoading } = useRugbyMatches('needs_review');
    const patchMatch = usePatchMatch();
    const refreshCatalog = useRefreshCatalog();
    const [expandedMatch, setExpandedMatch] = useState(null);
    if (matchesLoading)
        return _jsx("div", { className: "space-y-2", children: [0, 1].map((i) => _jsx(Skeleton, { className: "h-24 w-full" }, i)) });
    if (!matches || matches.length === 0) {
        return (_jsx("p", { className: "rounded-lg border border-border bg-card px-4 py-8 text-center text-[13px] text-muted-foreground", children: "Nothing to review. Videos with an uncertain match appear here." }));
    }
    const handleConfirm = (match) => {
        patchMatch.mutate({ mediaId: match.media_id, status: 'confirmed' }, {
            onSuccess: () => toast.success('Match confirmed'),
            onError: (e) => toast.error(e.message),
        });
    };
    const handleReject = (match) => {
        patchMatch.mutate({ mediaId: match.media_id, status: 'rejected' }, {
            onSuccess: () => toast.success('Match rejected'),
            onError: (e) => toast.error(e.message),
        });
    };
    const handleChangeFixture = (match, fixtureId) => {
        patchMatch.mutate({ mediaId: match.media_id, fixture_id: fixtureId, status: 'confirmed' }, {
            onSuccess: () => toast.success('Match reassigned'),
            onError: (e) => toast.error(e.message),
        });
        setExpandedMatch(null);
    };
    const handleRefresh = () => {
        refreshCatalog.mutate(undefined, {
            onSuccess: () => toast.success('Refresh scheduled'),
            onError: (e) => toast.error(e.message),
        });
    };
    return (_jsxs("section", { className: "rounded-lg border border-border bg-card", children: [_jsxs("div", { className: "flex h-11 items-center justify-between border-b border-border px-4", children: [_jsxs("h2", { className: "text-[13px] font-semibold", children: ["Match review ", _jsx("span", { className: "font-normal text-muted-foreground", children: matches.length })] }), _jsxs(Button, { onClick: handleRefresh, disabled: refreshCatalog.isPending, variant: "outline", size: "sm", className: "h-7 gap-1.5 px-2 text-[12px]", children: [_jsx(RotateCw, { className: "h-3.5 w-3.5" }), "Refresh leagues"] })] }), _jsx("ul", { className: "divide-y divide-border", children: matches.map((match) => (_jsxs("li", { className: "space-y-3 px-4 py-3 text-[13px]", children: [_jsxs("div", { className: "grid gap-3 sm:grid-cols-2", children: [_jsxs("div", { className: "min-w-0 space-y-0.5 rounded-md bg-muted/50 p-3", children: [_jsx("p", { className: "text-[12px] text-muted-foreground", children: "Source video" }), _jsx("p", { className: "break-words font-medium", title: match.source_name ?? undefined, children: match.source_name || match.source_caption || '-' }), match.source_caption && match.source_name && _jsx("p", { className: "line-clamp-2 text-[12px] text-muted-foreground", children: match.source_caption }), match.source_date && _jsxs("p", { className: "text-[12px] text-muted-foreground", title: absTime(match.source_date), children: ["Posted ", relTime(match.source_date)] })] }), _jsxs("div", { className: "min-w-0 space-y-0.5 rounded-md bg-muted/50 p-3", children: [_jsxs("p", { className: "text-[12px] text-muted-foreground", children: ["Suggested match, ", Math.round((match.confidence ?? 0) * 100), "% confident"] }), _jsxs("p", { className: "font-medium", children: [match.home_name, " vs ", match.away_name] }), _jsxs("p", { className: "text-[12px] text-muted-foreground", children: [match.season ?? '-', match.round ? `, round ${match.round}` : ''] })] })] }), expandedMatch === match.media_id ? (_jsx(FixtureSelector, { match: match, onSelect: (id) => handleChangeFixture(match, id), onCancel: () => setExpandedMatch(null) })) : (_jsxs("div", { className: "flex gap-2", children: [_jsx(Button, { onClick: () => handleConfirm(match), disabled: patchMatch.isPending, size: "sm", className: "h-8", children: "Confirm match" }), _jsx(Button, { onClick: () => setExpandedMatch(match.media_id), disabled: patchMatch.isPending, size: "sm", variant: "outline", className: "h-8", children: "Change fixture" }), _jsx(Button, { onClick: () => handleReject(match), disabled: patchMatch.isPending, size: "sm", variant: "ghost", className: "h-8 hover:text-err", children: "Reject match" })] }))] }, match.media_id))) })] }));
}
function FixtureSelector({ match, onSelect, onCancel, }) {
    const { data: fixtures, isLoading } = useLeagueFixtures(match.league_id, match.season);
    if (isLoading) {
        return _jsx("div", { className: "text-sm text-muted-foreground", children: "Loading fixtures\u2026" });
    }
    if (!fixtures || fixtures.length === 0) {
        return _jsx("div", { className: "text-[13px] text-muted-foreground", children: "No fixtures available for this season" });
    }
    return (_jsxs("div", { className: "space-y-2", children: [_jsx("p", { className: "text-[12px] text-muted-foreground", children: "Select the correct fixture" }), _jsxs(Select, { onValueChange: (val) => onSelect(parseInt(val)), children: [_jsx(SelectTrigger, { className: "w-full", children: _jsx(SelectValue, { placeholder: "Choose a fixture..." }) }), _jsx(SelectContent, { children: fixtures.map((fix) => (_jsxs(SelectItem, { value: fix.id.toString(), children: [fix.home_name, " vs ", fix.away_name, " (R", fix.round, ")"] }, fix.id))) })] }), _jsx("div", { className: "flex gap-2", children: _jsx(Button, { onClick: onCancel, size: "sm", variant: "outline", children: "Cancel" }) })] }));
}
