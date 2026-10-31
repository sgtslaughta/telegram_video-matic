import { useQuery } from '@tanstack/react-query';
async function get(url) {
    const r = await fetch(url, { credentials: 'include' });
    if (!r.ok)
        throw Object.assign(new Error(`HTTP ${r.status}`), { status: r.status });
    return r.json();
}
export function useOverview(hours) {
    return useQuery({
        queryKey: ['overview', hours],
        queryFn: () => get(`/api/overview?hours=${hours}`),
        refetchInterval: 30000,
    });
}
