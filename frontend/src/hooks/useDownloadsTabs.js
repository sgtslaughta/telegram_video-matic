import { useSearchParams } from 'react-router-dom';
export const TABS = ['queue', 'wanted', 'history', 'review'];
/** Active tab + history kind filter, both kept in the URL. */
export function useDownloadsTabs() {
    const [params, setParams] = useSearchParams();
    const raw = params.get('tab');
    const tab = TABS.includes(raw ?? '') ? raw : 'queue';
    const kind = params.get('kind') ?? '';
    const update = (patch) => {
        const next = new URLSearchParams(params);
        for (const [k, v] of Object.entries(patch)) {
            if (v)
                next.set(k, v);
            else
                next.delete(k);
        }
        setParams(next, { replace: true });
    };
    return {
        tab,
        kind,
        setTab: (t) => update({ tab: t === 'queue' ? null : t }),
        setKind: (k) => update({ kind: k || null }),
    };
}
