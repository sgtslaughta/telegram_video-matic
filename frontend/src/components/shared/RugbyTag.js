import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { MapPin } from 'lucide-react';
/** Compact inline rugby enrichment: team badges + "Home vs Away" + colored
 * round / venue chips. ponytail: one component for list rows + downloads;
 * cards keep their own larger layout. */
export function RugbyTag({ rugby, className = '' }) {
    if (!rugby)
        return null;
    return (_jsxs("span", { className: `inline-flex items-center gap-1.5 ${className}`, children: [rugby.home_badge && (_jsx("img", { src: rugby.home_badge, alt: rugby.home, className: "h-4 w-4 shrink-0 object-contain", loading: "lazy" })), rugby.away_badge && (_jsx("img", { src: rugby.away_badge, alt: rugby.away, className: "h-4 w-4 shrink-0 object-contain", loading: "lazy" })), _jsxs("span", { className: "truncate", children: [rugby.home, " vs ", rugby.away] }), rugby.round && (_jsxs("span", { className: "whitespace-nowrap rounded bg-brand/10 px-1.5 py-0.5 text-[10px] font-medium text-brand", children: ["R", rugby.round] })), rugby.venue && (_jsxs("span", { className: "inline-flex items-center gap-0.5 whitespace-nowrap rounded bg-ok/10 px-1.5 py-0.5 text-[10px] font-medium text-ok", children: [_jsx(MapPin, { className: "h-2.5 w-2.5" }), " ", rugby.venue] }))] }));
}
