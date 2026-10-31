import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useRescan } from '@/hooks/useSubscriptionTools';
import { Section } from './Section';
function RescanDialog({ id, open, onOpenChange }) {
    const [days, setDays] = useState('7');
    const rescan = useRescan(id);
    const n = Number(days);
    const valid = Number.isInteger(n) && n >= 1 && n <= 365;
    const run = async () => {
        try {
            const r = await rescan.mutateAsync(n);
            toast.success(`Rescan found ${r.found}, queued ${r.queued}, skipped ${r.skipped}`, { duration: 6000 });
            onOpenChange(false);
        }
        catch (e) {
            toast.error('Rescan failed', { description: e instanceof Error ? e.message : String(e), duration: Infinity });
        }
    };
    return (_jsx(Dialog, { open: open, onOpenChange: onOpenChange, children: _jsxs(DialogContent, { children: [_jsxs(DialogHeader, { children: [_jsx(DialogTitle, { children: "Rescan recent posts" }), _jsx(DialogDescription, { children: "Look back through the channel and queue anything the filter now allows." })] }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "rescanDays", className: "text-[13px] font-medium", children: "Days to look back" }), _jsx(Input, { id: "rescanDays", type: "number", min: 1, max: 365, value: days, onChange: (e) => setDays(e.target.value) }), !valid && _jsx("p", { role: "alert", className: "text-[12px] text-err", children: "Enter a number from 1 to 365." })] }), _jsxs(DialogFooter, { children: [_jsx(Button, { variant: "outline", onClick: () => onOpenChange(false), children: "Cancel" }), _jsx(Button, { onClick: run, disabled: !valid || rescan.isPending, children: rescan.isPending ? 'Rescanning…' : 'Rescan' })] })] }) }));
}
export function ToolsSection({ id }) {
    const [open, setOpen] = useState(false);
    return (_jsxs(Section, { title: "Tools", children: [_jsxs("div", { className: "flex items-center justify-between gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-[13px] font-medium", children: "Rescan recent posts" }), _jsx("p", { className: "text-[12px] text-muted-foreground", children: "Re-check history after changing the filter." })] }), _jsx(Button, { variant: "outline", size: "sm", onClick: () => setOpen(true), children: "Rescan" })] }), _jsx(RescanDialog, { id: id, open: open, onOpenChange: setOpen })] }));
}
