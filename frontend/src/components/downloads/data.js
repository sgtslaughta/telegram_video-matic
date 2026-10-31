import { useQuery } from '@tanstack/react-query';
import { fetchAPI } from '@/lib/api';
export const dq = {
    wanted: ['downloads', 'wanted'],
    failed: ['downloads', 'failed'],
    history: ['downloads', 'history'],
};
/** Rugby plugin may be absent: a 404/500 resolves to null so the section hides. */
export const useWanted = () => useQuery({
    queryKey: dq.wanted,
    queryFn: () => fetchAPI('/plugins/rugby/wanted').catch(() => null),
    refetchInterval: 30000,
});
export const useFailed = () => useQuery({
    queryKey: dq.failed,
    queryFn: () => fetchAPI('/wanted/failed'),
    refetchInterval: 30000,
});
export const post = (path, body) => fetchAPI(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });
/** Return a copy of `list` with the item at `from` moved to `to`. */
export function moveItem(list, from, to) {
    const next = list.slice();
    const [it] = next.splice(from, 1);
    next.splice(to, 0, it);
    return next;
}
