import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { clsx } from 'clsx';
export function EmptyState({ icon, title, message, action, className, }) {
    const defaultIcon = (_jsx("svg", { className: "h-12 w-12 text-muted-foreground", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" }) }));
    return (_jsxs("div", { className: clsx('flex flex-col items-center justify-center rounded-lg border border-dashed border-border px-6 py-12 text-center', className), children: [_jsx("div", { className: "mb-4", children: icon || defaultIcon }), _jsx("h3", { className: "text-lg font-semibold text-foreground", children: title }), _jsx("p", { className: "mt-2 text-sm text-muted-foreground", children: message }), action && (_jsx("button", { onClick: action.onClick, className: "mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90", children: action.label }))] }));
}
