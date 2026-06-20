import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'

export const channelKeys = {
  all: ['channels'] as const,
  list: () => [...channelKeys.all, 'list'] as const,
  topics: (channelId: number) => [...channelKeys.all, 'topics', channelId] as const,
}

export function useChannels() {
  return useQuery({
    queryKey: channelKeys.list(),
    queryFn: () => api.channels.list(),
  })
}

export function useTopics(channelId: number | null) {
  return useQuery({
    queryKey: channelKeys.topics(channelId || 0),
    queryFn: () => api.channels.topics(channelId!),
    enabled: !!channelId,
  })
}
