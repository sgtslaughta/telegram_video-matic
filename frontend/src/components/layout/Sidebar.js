import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, useLocation } from 'react-router-dom';
import { Moon, Sun, LogOut, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import Logo from '@/components/Logo';
import { useTheme } from '@/hooks/useTheme';
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads';
import * as api from '@/lib/api';
import { NAV, isActive } from './nav';
export default function Sidebar({ connected, onConnectClick, onSearch, }) {
    const { pathname } = useLocation();
    const { toggleTheme, effectiveTheme } = useTheme();
    const { data: active } = useActiveDownloads();
    const { data: queued } = useQueuedDownloads();
    const dlCount = (active?.length ?? 0) + (queued?.length ?? 0);
    const logout = async () => {
        await api.auth.logout().catch(() => { });
        window.location.href = '/login';
    };
    return (_jsxs("nav", { "aria-label": "Main", className: "hidden w-56 shrink-0 flex-col border-r border-border bg-card md:flex", children: [_jsxs("div", { className: "flex h-12 items-center gap-2 px-4", children: [_jsx(Logo, { className: "h-7 w-7" }), _jsx("span", { className: "text-[13px] font-semibold tracking-tight", children: "Video-matic" })] }), _jsxs("button", { onClick: onSearch, className: "mx-3 mb-2 flex h-8 items-center gap-2 rounded-md border border-border bg-background px-2.5 text-[13px] text-muted-foreground transition-colors hover:text-foreground", children: [_jsx(Search, { className: "h-3.5 w-3.5" }), _jsx("span", { className: "flex-1 text-left", children: "Search" }), _jsx("kbd", { className: "rounded border border-border px-1 text-[11px]", children: "\u2318K" })] }), _jsx("ul", { className: "flex-1 space-y-px px-2", children: NAV.map(({ label, href, icon: Icon }) => {
                    const on = isActive(pathname, href);
                    return (_jsx("li", { children: _jsxs(Link, { to: href, "aria-current": on ? 'page' : undefined, className: cn('relative flex h-8 items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors', on ? 'bg-brand/10 font-medium text-foreground' : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground'), children: [on && _jsx("span", { "aria-hidden": true, className: "absolute -left-2 top-1.5 bottom-1.5 w-[3px] rounded-r bg-brand" }), _jsx(Icon, { className: cn('h-4 w-4', on && 'text-brand'), strokeWidth: 1.75 }), _jsx("span", { className: "flex-1", children: label }), href === '/downloads' && dlCount > 0 && (_jsx("span", { className: "rounded-full bg-brand/15 px-1.5 text-[11px] font-medium tabular-nums text-brand", children: dlCount }))] }) }, href));
                }) }), _jsxs("div", { className: "space-y-px border-t border-border p-2", children: [_jsxs("button", { onClick: onConnectClick, className: "flex h-8 w-full items-center gap-2.5 rounded-md px-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground", children: [_jsx("span", { className: cn('h-2 w-2 rounded-full', connected ? 'bg-ok' : 'bg-err') }), _jsx("span", { className: "flex-1 text-left", children: connected ? 'Telegram connected' : 'Telegram offline' })] }), _jsxs("div", { className: "flex gap-px", children: [_jsxs("button", { onClick: toggleTheme, "aria-label": effectiveTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme', className: "flex h-8 flex-1 items-center gap-2.5 rounded-md px-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground", children: [effectiveTheme === 'dark' ? _jsx(Sun, { className: "h-4 w-4" }) : _jsx(Moon, { className: "h-4 w-4" }), "Theme"] }), _jsx("button", { onClick: logout, "aria-label": "Log out", className: "flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground", children: _jsx(LogOut, { className: "h-4 w-4" }) })] })] })] }));
}
export function MobileNav() {
    const { pathname } = useLocation();
    return (_jsx("nav", { "aria-label": "Main", className: "fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-card md:hidden", children: NAV.slice(0, 5).map(({ label, href, icon: Icon }) => {
            const on = isActive(pathname, href);
            return (_jsxs(Link, { to: href, "aria-current": on ? 'page' : undefined, className: cn('flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px]', on ? 'font-medium text-brand' : 'text-muted-foreground'), children: [_jsx(Icon, { className: "h-5 w-5", strokeWidth: 1.75 }), label] }, href));
        }) }));
}
