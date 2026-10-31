import { useQuery } from '@tanstack/react-query';
// /api/health answers 503 with a JSON body when sync is unhealthy; read it either way.
export function useHealth() {
    return useQuery({
        queryKey: ['health'],
        queryFn: async () => (await fetch('/api/health', { credentials: 'include' })).json(),
        refetchInterval: 30000,
    });
}
