import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Command } from 'cmdk';
import { Moon, Rss } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog';
import { useTheme } from '@/hooks/useTheme';
import { useSubscriptions } from '@/hooks/useSubscriptions';
import { NAV } from './nav';
const item = 'flex h-9 cursor-pointer items-center gap-2.5 rounded-md px-2.5 text-[13px] text-muted-foreground aria-selected:bg-accent aria-selected:text-foreground';
const group = '[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:text-muted-foreground';
export default function CommandPalette({ open, onOpenChange }) {
    const navigate = useNavigate();
    const { toggleTheme } = useTheme();
    const { data: subs } = useSubscriptions();
    useEffect(() => {
        const onKey = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                onOpenChange(!open);
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [open, onOpenChange]);
    const go = (href) => {
        onOpenChange(false);
        navigate(href);
    };
    return (_jsx(Dialog, { open: open, onOpenChange: onOpenChange, children: _jsxs(DialogContent, { className: "top-[20%] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-lg", children: [_jsx(DialogTitle, { className: "sr-only", children: "Search" }), _jsxs(Command, { loop: true, className: "flex flex-col", children: [_jsx(Command.Input, { autoFocus: true, placeholder: "Go to a page or subscription", className: "h-11 border-b border-border bg-transparent px-4 text-[14px] outline-none placeholder:text-muted-foreground" }), _jsxs(Command.List, { className: "max-h-80 overflow-y-auto p-1.5", children: [_jsx(Command.Empty, { className: "px-3 py-6 text-center text-[13px] text-muted-foreground", children: "Nothing matches. Try a page name or a subscription." }), _jsx(Command.Group, { heading: "Pages", className: group, children: NAV.map(({ label, href, icon: Icon, keys }) => (_jsxs(Command.Item, { value: label, onSelect: () => go(href), className: item, children: [_jsx(Icon, { className: "h-4 w-4", strokeWidth: 1.75 }), _jsx("span", { className: "flex-1", children: label }), _jsxs("kbd", { className: "text-[11px]", children: ["G ", keys.toUpperCase()] })] }, href))) }), !!subs?.length && (_jsx(Command.Group, { heading: "Subscriptions", className: group, children: subs.map((s) => (_jsxs(Command.Item, { value: `sub ${s.name ?? ''} ${s.channel_title ?? ''} ${s.topic_title ?? ''}`, onSelect: () => go(`/subscriptions/${s.id}`), className: item, children: [_jsx(Rss, { className: "h-4 w-4", strokeWidth: 1.75 }), _jsx("span", { className: "flex-1 truncate", children: s.name || s.topic_title || s.channel_title })] }, s.id))) })), _jsx(Command.Group, { heading: "Actions", className: group, children: _jsxs(Command.Item, { value: "toggle theme", onSelect: () => { toggleTheme(); onOpenChange(false); }, className: item, children: [_jsx(Moon, { className: "h-4 w-4", strokeWidth: 1.75 }), "Toggle light and dark theme"] }) })] })] })] }) }));
}
