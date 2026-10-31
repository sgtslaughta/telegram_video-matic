import { useQuery } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const eventKeys = {
    all: ['events'],
    filtered: (filters) => [...eventKeys.all, filters],
};
export function useEvents(filters) {
    return useQuery({
        queryKey: eventKeys.filtered(filters || {}),
        queryFn: () => api.events.list(filters),
        refetchInterval: 5000,
    });
}
