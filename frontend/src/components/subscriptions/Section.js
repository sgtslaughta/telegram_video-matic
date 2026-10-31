import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
export function Section({ title, description, children, className }) {
    return (_jsxs("section", { className: cn('rounded-lg border border-border bg-card', className), children: [_jsxs("div", { className: "border-b border-border px-4 py-3", children: [_jsx("h2", { className: "text-[13px] font-semibold", children: title }), description && _jsx("p", { className: "mt-0.5 text-[12px] text-muted-foreground", children: description })] }), _jsx("div", { className: "space-y-4 p-4", children: children })] }));
}
export function Field({ label, htmlFor, hint, error, children }) {
    return (_jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: htmlFor, className: "text-[13px] font-medium", children: label }), children, error
                ? _jsx("p", { role: "alert", className: "text-[12px] text-err", children: error })
                : hint && _jsx("p", { className: "text-[12px] text-muted-foreground", children: hint })] }));
}
export function ToggleRow({ id, label, hint, checked, onChange }) {
    return (_jsxs("div", { className: "flex items-center justify-between gap-4", children: [_jsxs("div", { className: "min-w-0", children: [_jsx(Label, { htmlFor: id, className: "text-[13px] font-medium", children: label }), hint && _jsx("p", { className: "text-[12px] text-muted-foreground", children: hint })] }), _jsx(Switch, { id: id, checked: checked, onCheckedChange: onChange })] }));
}
