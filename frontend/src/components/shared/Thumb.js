import { jsx as _jsx } from "react/jsx-runtime";
import { useState } from 'react';
import { Film } from 'lucide-react';
import { cn } from '@/lib/utils';
/** Media thumbnail. Always asks the server (it fetches + caches from Telegram
 * on first request); falls back to a film icon if there is none. */
export function Thumb({ id, className }) {
    const [failed, setFailed] = useState(false);
    return (_jsx("div", { className: cn('flex items-center justify-center overflow-hidden rounded bg-muted', className), children: failed
            ? _jsx(Film, { className: "h-4 w-4 text-muted-foreground/60", strokeWidth: 1.5 })
            : _jsx("img", { src: `/api/media/${id}/thumb`, alt: "", loading: "lazy", onError: () => setFailed(true), className: "h-full w-full object-cover" }) }));
}
