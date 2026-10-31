import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const channelsKeys = {
    all: ['channels'],
    list: () => [...channelsKeys.all, 'list'],
};
export const topicsKeys = {
    all: ['topics'],
    byChannel: (channelId) => [...topicsKeys.all, channelId],
};
export function useChannels() {
    return useQuery({
        queryKey: channelsKeys.list(),
        queryFn: () => api.channels.list(),
    });
}
export function useTopics(channelId) {
    return useQuery({
        queryKey: topicsKeys.byChannel(channelId || 0),
        queryFn: () => api.channels.topics(channelId),
        enabled: channelId != null,
    });
}
export function useBrowse(channelId, topicId) {
    return useInfiniteQuery({
        queryKey: ['browse', channelId || 0, topicId || 0],
        queryFn: ({ pageParam }) => api.channels.browse(channelId, {
            topic_id: topicId ?? undefined,
            limit: 50,
            offset_id: pageParam,
        }),
        initialPageParam: 0,
        getNextPageParam: (last) => last.has_more && last.next_offset_id ? last.next_offset_id : undefined,
        enabled: channelId != null,
        staleTime: 30000,
    });
}
