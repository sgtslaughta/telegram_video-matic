import { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { fetchAPI } from '@/lib/api';
export function useDebounced(value, ms) {
    const [v, setV] = useState(value);
    useEffect(() => {
        const t = setTimeout(() => setV(value), ms);
        return () => clearTimeout(t);
    }, [value, ms]);
    return v;
}
/** Live filter preview. Pass null to disable; requests are debounced 600ms. */
export function useFilterPreview(params) {
    const key = useDebounced(params ? JSON.stringify(params) : null, 600);
    return useQuery({
        queryKey: ['filter-preview', key],
        queryFn: () => fetchAPI('/subscriptions/preview-filter', { method: 'POST', body: key }),
        enabled: key !== null,
        retry: false,
        staleTime: 30000,
    });
}
export function useRescan(id) {
    return useMutation({
        mutationFn: (days) => fetchAPI(`/subscriptions/${id}/rescan`, { method: 'POST', body: JSON.stringify({ days }) }),
    });
}
