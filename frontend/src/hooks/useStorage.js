import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '@/lib/api';
const KEY = ['storage'];
export function useStorage() {
    return useQuery({ queryKey: KEY, queryFn: () => fetchAPI('/storage'), refetchInterval: 60000 });
}
export function usePruneConfirm() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => fetchAPI('/storage/prune/confirm', { method: 'POST' }),
        onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
    });
}
export function useDeleteUntracked() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (path) => fetchAPI('/storage/untracked', { method: 'DELETE', body: JSON.stringify({ path }) }),
        onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
    });
}
