import { useQuery } from '@tanstack/react-query';
import { fetchAPI } from '@/lib/api';
export function useSummary() {
    return useQuery({ queryKey: ['summary'], queryFn: () => fetchAPI('/summary'), staleTime: Infinity });
}
export const markSeen = () => fetchAPI('/summary/seen', { method: 'POST' });
