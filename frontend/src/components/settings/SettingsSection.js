import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
/** Settings panel. The footer with "Save changes" only appears when dirty. */
export function SettingsSection({ id, title, description, dirty, saving, onSave, children }) {
    return (_jsxs("section", { id: id, className: "scroll-mt-6 rounded-lg border border-border bg-card", children: [_jsxs("div", { className: "border-b border-border px-4 py-3", children: [_jsx("h2", { className: "text-[13px] font-semibold", children: title }), description && _jsx("p", { className: "mt-0.5 text-[12px] text-muted-foreground", children: description })] }), _jsx("div", { className: "space-y-5 p-4", children: children }), dirty && onSave && (_jsx("div", { className: "flex justify-end border-t border-border px-4 py-2.5", children: _jsx(Button, { size: "sm", onClick: onSave, disabled: saving, children: saving ? 'Saving…' : 'Save changes' }) }))] }));
}
export function Field({ id, label, help, children }) {
    return (_jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: id, className: "text-[13px] font-medium", children: label }), children, help && _jsx("p", { className: "text-[12px] text-muted-foreground", children: help })] }));
}
export const inputCls = 'h-9 max-w-xs text-[13px]';
