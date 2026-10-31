import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/** Page title row: title + optional one-line description, actions right-aligned. */
export function PageHeader({ title, description, actions }) {
    return (_jsxs("header", { className: "flex flex-wrap items-end justify-between gap-3 pb-5", children: [_jsxs("div", { className: "min-w-0", children: [_jsx("h1", { className: "text-[20px] font-semibold leading-7 tracking-tight", children: title }), description && _jsx("p", { className: "mt-0.5 text-[13px] text-muted-foreground", children: description })] }), actions && _jsx("div", { className: "flex items-center gap-2", children: actions })] }));
}
/** Standard page body width + padding (bottom pad clears the mobile nav). */
export function Page({ children, wide }) {
    return _jsx("div", { className: `mx-auto w-full px-5 pb-24 pt-6 md:px-8 md:pb-10 ${wide ? 'max-w-[1400px]' : 'max-w-[1100px]'}`, children: children });
}
