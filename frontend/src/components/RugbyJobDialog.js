import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useRugbyJobReport, useRugbyRunJob } from '@/hooks/useRugby';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ProgressBar } from '@/components/shared/ProgressBar';
import { toast } from 'sonner';
const COPY = {
    import: {
        title: 'Import library files',
        blurb: 'Adds video files already on disk (not downloaded by TVM) and matches them. Nothing moves.',
        apply: 'Import',
    },
    rematch: {
        title: 'Re-match games',
        blurb: 'Retries unmatched games and re-scores auto matches (confirmed ones are kept), asking the API for missing fixtures. Applying files matched games.',
        apply: 'Apply matches',
    },
    reconcile: {
        title: 'Reorganize library',
        blurb: 'Moves every rugby video into its league / Season folder and rewrites Jellyfin metadata. Existing files are never overwritten.',
        apply: 'Move files',
    },
};
/** Last `n` path segments — enough to see league/Season/file. */
const tail = (p, n = 3) => (p ? p.split('/').slice(-n).join('/') : '');
function Row({ row }) {
    const moves = row.to && row.from && row.to !== row.from;
    return (_jsxs("li", { className: "border-b py-2 text-xs last:border-0", children: [row.file && _jsx("p", { className: "font-medium", children: row.file }), row.fixture && (_jsxs("p", { className: "text-muted-foreground", children: [row.status === 'needs_review' ? 'Review: ' : '', row.fixture, row.previous && _jsxs("span", { className: "line-through", children: [" (was ", row.previous, ")"] })] })), row.status === 'none' && _jsx("p", { className: "text-muted-foreground", children: "No fixture found" }), moves ? (_jsxs("p", { className: "break-all", children: [_jsx("span", { className: "text-muted-foreground", children: tail(row.from) }), " \u2192 ", tail(row.to)] })) : row.from && row.to ? (_jsx("p", { className: "text-muted-foreground", children: "Stays in place" })) : null] }));
}
/** Preview-then-apply runner: opening starts a dry run and shows its plan;
 * Apply runs the job for real. */
export function RugbyJobDialog({ job, onClose }) {
    const run = useRugbyRunJob();
    const [phase, setPhase] = useState('preview');
    const report = useRugbyJobReport(job, true);
    const rep = report.data;
    // Mounted per job (keyed by the parent), so this runs once per open.
    useEffect(() => {
        run.mutate({ job, dryRun: true }, {
            // 409: already running (e.g. reopened) — just keep showing its progress.
            onError: (e) => {
                const msg = e instanceof Error ? e.message : 'Could not start preview';
                if (!msg.includes('already running'))
                    toast.error(msg);
            },
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [job]);
    const copy = COPY[job];
    const running = run.isPending || !rep || rep.running;
    const ready = !running && (!!rep?.error || rep?.dry_run === (phase === 'preview'));
    const rows = rep?.plan ?? [];
    const files = rep?.files ?? [];
    const conflicts = rep?.conflicts ?? [];
    const apply = () => {
        setPhase('apply');
        run.mutate({ job, dryRun: false }, {
            onError: (e) => toast.error(e instanceof Error ? e.message : 'Could not start job'),
        });
    };
    const summary = ready && rep
        ? Object.entries(rep)
            .filter(([k, v]) => typeof v === 'number' && !['done', 'total'].includes(k))
            .map(([k, v]) => `${k.replace('_', ' ')}: ${v}`)
            .join(' · ')
        : '';
    return (_jsx(Dialog, { open: true, onOpenChange: (o) => !o && onClose(), children: _jsxs(DialogContent, { className: "max-w-3xl", children: [_jsxs(DialogHeader, { children: [_jsxs(DialogTitle, { children: [copy.title, phase === 'preview' ? ' — preview' : ''] }), _jsx(DialogDescription, { children: copy.blurb })] }), running || !ready ? (_jsxs("div", { className: "space-y-2 py-4 text-sm", children: [_jsxs("p", { children: [phase === 'preview' ? 'Building plan…' : 'Applying…', ' ', rep?.total ? `${rep.done} / ${rep.total}` : ''] }), !!rep?.total && _jsx(ProgressBar, { progress: ((rep.done ?? 0) / rep.total) * 100 }), _jsx("p", { className: "text-xs text-muted-foreground", children: "API lookups are rate limited; large libraries take a while. You can close this \u2014 the job keeps running." })] })) : rep?.error ? (_jsxs("p", { className: "py-4 text-sm text-red-600", children: ["Failed: ", rep.error] })) : (_jsxs("div", { className: "space-y-2", children: [_jsx("p", { className: "text-sm", children: summary }), conflicts.length > 0 && (_jsxs("p", { className: "text-sm text-amber-600", children: [conflicts.length, " file(s) skipped: destination already exists (duplicates)."] })), _jsxs("ul", { className: "max-h-[50vh] overflow-y-auto rounded border px-3", children: [rows.map((r) => _jsx(Row, { row: r }, `${r.media_id}-${r.to}`)), files.map((f) => _jsx("li", { className: "border-b py-2 text-xs last:border-0", children: f }, f)), rows.length + files.length === 0 && (_jsx("li", { className: "py-4 text-center text-sm text-muted-foreground", children: "Nothing to do" }))] })] })), _jsxs(DialogFooter, { children: [_jsx(Button, { variant: "outline", onClick: onClose, children: phase === 'apply' && ready ? 'Done' : 'Cancel' }), phase === 'preview' && (_jsx(Button, { onClick: apply, disabled: !ready || !!rep?.error || rows.length + files.length === 0, children: copy.apply }))] })] }) }));
}
