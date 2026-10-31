import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import Logo from '@/components/Logo';
import TelegramLoginFlow from '@/components/telegram/TelegramLoginFlow';
export default function Connect() {
    return (_jsx("div", { className: "flex min-h-[70vh] items-center justify-center px-4 py-8", children: _jsxs("div", { className: "w-full max-w-md", children: [_jsxs("div", { className: "mb-6 flex flex-col items-center gap-2 text-center", children: [_jsx(Logo, { className: "h-16 w-16", title: "TGVM" }), _jsx("h1", { className: "text-[20px] font-semibold tracking-tight", children: "Connect Telegram" }), _jsx("p", { className: "text-[13px] text-muted-foreground", children: "Sign in to the account that can see your channels." })] }), _jsx(TelegramLoginFlow, {})] }) }));
}
