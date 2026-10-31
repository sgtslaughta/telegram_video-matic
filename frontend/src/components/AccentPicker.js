import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Check } from 'lucide-react';
import { useAccent } from '@/hooks/useAccent';
import { ACCENTS } from '@/lib/accent';
import { cn } from '@/lib/utils';
export default function AccentPicker() {
    const { accent, setAccent } = useAccent();
    return (_jsx("div", { role: "radiogroup", "aria-label": "Accent color", className: "flex flex-wrap gap-2", children: ACCENTS.map((a) => (_jsxs("button", { role: "radio", "aria-checked": accent === a.name, onClick: () => setAccent(a.name), className: cn('flex items-center gap-2 rounded-md border px-3 py-1.5 text-[13px] transition-colors', accent === a.name ? 'border-brand bg-brand/10 font-medium text-brand' : 'border-border text-muted-foreground hover:text-foreground'), children: [_jsx("span", { className: "flex h-4 w-4 items-center justify-center rounded-full border border-border", style: { backgroundColor: a.swatch }, children: accent === a.name && _jsx(Check, { className: "h-2.5 w-2.5 text-white", strokeWidth: 3 }) }), a.label] }, a.name))) }));
}
