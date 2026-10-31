import { useState, useMemo } from 'react';
const DEFAULTS = {
    channelId: null,
    topicId: null,
    name: '',
    filterMode: 'include',
    filterRegex: '',
    regexError: null,
    checkFrequency: '5m',
    scheduleDays: [],
    minSizeMb: null,
    maxSizeMb: null,
    maxTotalGb: null,
    dateFrom: '',
    dateTo: '',
    ongoing: true,
    storagePath: '',
    renameTemplate: '{channel}/{title}.{ext}',
    retentionDays: null,
    seasonDetection: false,
    jellyfinMetadata: false,
    keep: false,
};
export function useSubscriptionEditor(initialState, resetKey) {
    const [state, setState] = useState({ ...DEFAULTS, ...initialState });
    const [base, setBase] = useState(state);
    // The edit form mounts before the query resolves, so the first init uses
    // defaults. Re-seed from initialState once the loaded sub (resetKey) changes.
    const [seenKey, setSeenKey] = useState(resetKey);
    if (seenKey !== resetKey) {
        setSeenKey(resetKey);
        if (initialState) {
            const seeded = { ...DEFAULTS, ...initialState };
            setState(seeded);
            setBase(seeded);
        }
    }
    // Live regex validation
    const regexStatus = useMemo(() => {
        if (!state.filterRegex)
            return null;
        try {
            new RegExp(state.filterRegex);
            return { valid: true, error: null };
        }
        catch (e) {
            return { valid: false, error: e.message };
        }
    }, [state.filterRegex]);
    const update = (key, value) => {
        setState((prev) => ({ ...prev, [key]: value }));
    };
    const toggleScheduleDay = (day) => {
        setState((prev) => ({
            ...prev,
            scheduleDays: prev.scheduleDays.includes(day)
                ? prev.scheduleDays.filter((d) => d !== day)
                : [...prev.scheduleDays, day],
        }));
    };
    const dirty = useMemo(() => JSON.stringify(state) !== JSON.stringify(base), [state, base]);
    return {
        state,
        dirty,
        discard: () => setState(base),
        markSaved: () => setBase(state),
        update,
        toggleScheduleDay,
        regexValid: regexStatus?.valid ?? true,
        regexError: regexStatus?.error,
    };
}
