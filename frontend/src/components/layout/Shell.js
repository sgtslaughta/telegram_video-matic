import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useRef, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar, { MobileNav } from './Sidebar';
import CommandPalette from './CommandPalette';
import WelcomeSplash from './WelcomeSplash';
import { NAV } from './nav';
import TelegramLoginDialog from '@/components/telegram/TelegramLoginDialog';
import { useTgStatus } from '@/hooks/useTgStatus';
import { useHealth } from '@/hooks/useHealth';
import { AccountStatus } from '@/lib/types';
import { relTime } from '@/lib/format';
import { toast } from 'sonner';
function useGoShortcuts() {
    const navigate = useNavigate();
    const pending = useRef(0);
    useEffect(() => {
        const onKey = (e) => {
            const t = e.target;
            if (e.metaKey || e.ctrlKey || e.altKey || t.closest('input, textarea, select, [contenteditable]'))
                return;
            if (e.key === 'g') {
                pending.current = Date.now();
                return;
            }
            if (Date.now() - pending.current < 1000) {
                const hit = NAV.find((n) => n.keys === e.key);
                if (hit)
                    navigate(hit.href);
                pending.current = 0;
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [navigate]);
}
function Banner() {
    const { data: health, error } = useHealth();
    const prev = useRef(undefined);
    useEffect(() => {
        const now = health?.status;
        if (prev.current && prev.current !== 'ok' && now === 'ok')
            toast.success('Sync is back to normal');
        prev.current = now;
    }, [health?.status]);
    let msg = null;
    if (error)
        msg = 'Can’t reach the server. Retrying every 30 seconds.';
    else if (health?.status === 'down')
        msg = 'Telegram is disconnected. Sync is paused and reconnecting automatically.';
    else if (health?.status === 'stale')
        msg = `Sync hasn’t completed ${health.last_ok_poll_at ? `since ${relTime(health.last_ok_poll_at)}` : 'yet'}. Check Activity for errors.`;
    if (!msg)
        return null;
    return (_jsxs("div", { role: "status", className: "flex items-center gap-2 border-b border-err/30 bg-err/10 px-5 py-2 text-[13px] text-foreground md:px-8", children: [_jsx("span", { className: "h-2 w-2 shrink-0 rounded-full bg-err" }), msg] }));
}
export default function Shell() {
    const { data: tg } = useTgStatus();
    const [loginOpen, setLoginOpen] = useState(false);
    const [searchOpen, setSearchOpen] = useState(false);
    const connected = tg?.status === AccountStatus.CONNECTED;
    useGoShortcuts();
    useEffect(() => {
        if (tg && !connected)
            setLoginOpen(true);
    }, [tg, connected]);
    return (_jsxs("div", { className: "flex h-screen bg-background text-foreground", children: [_jsx(Sidebar, { connected: connected, onConnectClick: () => setLoginOpen(true), onSearch: () => setSearchOpen(true) }), _jsxs("div", { className: "flex min-w-0 flex-1 flex-col", children: [_jsx(Banner, {}), _jsx("main", { className: "flex-1 overflow-auto", children: _jsx(Outlet, {}) })] }), _jsx(MobileNav, {}), _jsx(CommandPalette, { open: searchOpen, onOpenChange: setSearchOpen }), _jsx(WelcomeSplash, {}), _jsx(TelegramLoginDialog, { open: loginOpen, onOpenChange: setLoginOpen })] }));
}
