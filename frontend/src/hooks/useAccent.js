import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useEffect, useState } from 'react';
import { ACCENTS, DEFAULT_ACCENT, applyAccent } from '@/lib/accent';
// v2: brand moved to Telegram blue; ignore the old saved (violet) choice once.
const KEY = 'accent.v2';
const AccentContext = createContext(null);
export function AccentProvider({ children }) {
    const [accent, setAccent] = useState(() => {
        const saved = typeof localStorage !== 'undefined' ? localStorage.getItem(KEY) : null;
        return saved && ACCENTS.some((a) => a.name === saved) ? saved : DEFAULT_ACCENT;
    });
    useEffect(() => {
        applyAccent(accent);
        localStorage.setItem(KEY, accent);
    }, [accent]);
    return _jsx(AccentContext.Provider, { value: { accent, setAccent }, children: children });
}
export function useAccent() {
    const ctx = useContext(AccentContext);
    // ponytail: graceful fallback so components render in isolation (tests) without a provider
    if (!ctx)
        return { accent: DEFAULT_ACCENT, setAccent: () => { } };
    return ctx;
}
