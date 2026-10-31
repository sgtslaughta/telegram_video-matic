import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button } from '@/components/ui/button';
/** Sticky footer, only rendered while the form has unsaved changes. */
export function SaveBar({ onSave, onDiscard, saving, label }) {
    return (_jsxs("div", { role: "region", "aria-label": "Unsaved changes", className: "sticky bottom-4 z-30 mt-6 flex h-12 items-center justify-between gap-3 rounded-lg border border-border bg-card px-4", children: [_jsx("p", { className: "text-[13px] text-muted-foreground", children: "You have unsaved changes." }), _jsxs("div", { className: "flex gap-2", children: [_jsx(Button, { variant: "outline", size: "sm", onClick: onDiscard, disabled: saving, children: "Discard" }), _jsx(Button, { size: "sm", onClick: onSave, disabled: saving, children: saving ? 'Saving…' : label })] })] }));
}
