import { useQuery } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const channelKeys = {
    all: ['channels'],
    list: () => [...channelKeys.all, 'list'],
    topics: (channelId) => [...channelKeys.all, 'topics', channelId],
};
export function useChannels() {
    return useQuery({
        queryKey: channelKeys.list(),
        queryFn: () => api.channels.list(),
    });
}
export function useTopics(channelId) {
    return useQuery({
        queryKey: channelKeys.topics(channelId || 0),
        queryFn: () => api.channels.topics(channelId),
        enabled: !!channelId,
    });
}
