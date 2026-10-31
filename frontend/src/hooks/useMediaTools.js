import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '@/lib/api';
import { mediaKeys } from '@/hooks/useMedia';
export function useMediaFull(id) {
    return useQuery({
        queryKey: mediaKeys.detail(id),
        queryFn: () => fetchAPI(`/media/${id}`),
        enabled: id > 0,
    });
}
export function useMediaHistory(id) {
    return useQuery({
        queryKey: ['media', 'history', id],
        queryFn: () => fetchAPI('/history', { params: { media_id: id } }),
        enabled: id > 0,
    });
}
export function useSetKeep(id) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (keep) => fetchAPI(`/media/${id}/keep`, { method: 'PATCH', body: JSON.stringify({ keep }) }),
        onSuccess: () => qc.invalidateQueries({ queryKey: mediaKeys.detail(id) }),
    });
}
const typing = (t) => {
    const el = t;
    return !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable);
};
/** j/k move, Enter opens, `/` focuses the search input. Rows carry data-nav="<index>". */
export function useListNav(count, onOpen) {
    const [active, setActive] = useState(-1);
    const searchRef = useRef(null);
    const openRef = useRef(onOpen);
    useEffect(() => { openRef.current = onOpen; });
    const move = useCallback((d) => {
        setActive((i) => Math.max(0, Math.min(count - 1, i + d)));
    }, [count]);
    useEffect(() => {
        const onKey = (e) => {
            if (e.metaKey || e.ctrlKey || e.altKey || typing(e.target))
                return;
            if (e.key === '/') {
                e.preventDefault();
                searchRef.current?.focus();
            }
            else if (e.key === 'j')
                move(1);
            else if (e.key === 'k')
                move(-1);
            else if (e.key === 'Enter' && active >= 0 && active < count && !e.target.closest?.('button,a,[role=button]')) {
                openRef.current(active);
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [move, active, count]);
    useEffect(() => {
        if (active >= 0)
            document.querySelector(`[data-nav="${active}"]`)?.scrollIntoView?.({ block: 'nearest' });
    }, [active]);
    return { active, setActive, searchRef };
}
