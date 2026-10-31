import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { usePruneConfirm } from '@/hooks/useStorage';
import { withToast } from '@/lib/toast';
import { DestructiveConfirm } from './DestructiveConfirm';
export function PausedPanel({ count, gb, onReview }) {
    const [open, setOpen] = useState(false);
    const prune = usePruneConfirm();
    const noun = `${count} file${count === 1 ? '' : 's'}`;
    const run = async () => {
        setOpen(false);
        await withToast(() => prune.mutateAsync(), { success: `Deleted ${noun}` });
    };
    return (_jsxs("section", { className: "flex flex-wrap items-center gap-4 rounded-lg border border-warn/40 bg-warn/10 p-4", children: [_jsx(AlertTriangle, { className: "h-5 w-5 shrink-0 text-warn", strokeWidth: 1.75 }), _jsxs("div", { className: "min-w-0 flex-1", children: [_jsxs("h2", { className: "text-[13px] font-semibold", children: ["Cleanup is paused: ", noun, " (", gb, " GB) would be deleted"] }), _jsx("p", { className: "text-[12px] text-muted-foreground", children: "Nothing is removed until you approve it." })] }), _jsxs("div", { className: "flex gap-2", children: [_jsx(Button, { variant: "outline", size: "sm", onClick: onReview, children: "Review list" }), _jsxs(Button, { variant: "destructive", size: "sm", disabled: prune.isPending, onClick: () => setOpen(true), children: ["Delete ", noun] })] }), _jsx(DestructiveConfirm, { open: open, title: `Delete ${noun}?`, description: `This permanently deletes ${noun} (${gb} GB) from disk. It can’t be undone.`, confirmText: `Delete ${noun}`, onConfirm: run, onCancel: () => setOpen(false) })] }));
}
