import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { cn } from '@/lib/utils';
export function Panel({ title, aside, children, className, id }) {
    return (_jsxs("section", { id: id, className: cn('min-w-0 rounded-lg border border-border bg-card', className), children: [_jsxs("div", { className: "flex h-11 items-center justify-between border-b border-border px-4", children: [_jsx("h2", { className: "text-[13px] font-semibold", children: title }), aside && _jsx("span", { className: "text-[12px] text-muted-foreground", children: aside })] }), children] }));
}
export const TH = 'h-9 px-4 text-left text-[12px] font-normal text-muted-foreground';
export const TD = 'h-10 px-4';
