import { useInfiniteQuery } from '@tanstack/react-query';
import { fetchAPI } from '@/lib/api';
export const PAGE = 50;
/** Offset-paginated events; key starts with ['events'] so live invalidation refreshes it. */
export function useEventsFeed(f) {
    return useInfiniteQuery({
        queryKey: ['events', 'feed', f],
        initialPageParam: 0,
        queryFn: ({ pageParam }) => fetchAPI('/events', {
            params: { limit: PAGE, offset: pageParam, ...(f.level && { level: f.level }), ...(f.kind && { kind: f.kind }) },
        }),
        getNextPageParam: (last, all) => (last.length === PAGE ? all.length * PAGE : undefined),
        refetchInterval: 15000,
    });
}
