import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, } from '@/components/ui/dialog';
import TelegramLoginFlow from './TelegramLoginFlow';
export default function TelegramLoginDialog({ open, onOpenChange, }) {
    return (_jsx(Dialog, { open: open, onOpenChange: onOpenChange, children: _jsxs(DialogContent, { className: "sm:max-w-md", children: [_jsxs(DialogHeader, { children: [_jsx(DialogTitle, { children: "Connect Telegram" }), _jsx(DialogDescription, { children: "Sign in to your Telegram account to start syncing media." })] }), _jsx(TelegramLoginFlow, { onConnected: () => onOpenChange(false) })] }) }));
}
