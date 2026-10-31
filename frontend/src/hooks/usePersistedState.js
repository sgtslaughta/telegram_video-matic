import { useEffect, useState } from 'react';
// useState that survives reloads/navigation by syncing to localStorage.
// ponytail: JSON round-trip; fine for the small UI-pref values we store.
export function usePersistedState(key, initial) {
    const [value, setValue] = useState(() => {
        try {
            const raw = localStorage.getItem(key);
            return raw !== null ? JSON.parse(raw) : initial;
        }
        catch {
            return initial;
        }
    });
    useEffect(() => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        }
        catch {
            // storage full / unavailable — non-fatal, just don't persist
        }
    }, [key, value]);
    return [value, setValue];
}
