import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useTgStatus } from '@/hooks/useTgStatus';
import { AccountStatus } from '@/lib/types';
import { cn } from '@/lib/utils';
import { SettingsSection } from './SettingsSection';
export function AccountSection() {
    const { data } = useTgStatus();
    const connected = data?.status === AccountStatus.CONNECTED;
    const who = data?.username ? `@${data.username}` : data?.display_name;
    return (_jsx(SettingsSection, { id: "account", title: "Account", description: "The Telegram account used to find and download videos.", children: _jsxs("div", { className: "flex items-center justify-between gap-3", children: [_jsxs("div", { className: "flex min-w-0 items-center gap-2.5", children: [_jsx("span", { className: cn('h-2 w-2 shrink-0 rounded-full', connected ? 'bg-ok' : data?.configured ? 'bg-warn' : 'bg-idle') }), _jsxs("div", { className: "min-w-0 text-[13px]", children: [_jsx("p", { className: "truncate font-medium", children: connected ? `Connected${who ? ` as ${who}` : ''}` : data?.configured ? 'Not signed in' : 'Not set up' }), connected && data?.phone && _jsx("p", { className: "text-[12px] text-muted-foreground", children: data.phone })] })] }), _jsx(Button, { asChild: true, size: "sm", variant: "outline", className: "h-8 text-[13px]", children: _jsx(Link, { to: "/connect", children: connected ? 'Manage account' : 'Connect Telegram' }) })] }) }));
}
