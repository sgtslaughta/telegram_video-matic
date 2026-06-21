import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'

export const downloadKeys = {
  active: () => ['downloads', 'active'] as const,
  queued: () => ['downloads', 'queued'] as const,
}

export function useQueuedDownloads() {
  return useQuery({
    queryKey: downloadKeys.queued(),
    queryFn: () => api.downloads.queued(),
    refetchInterval: 2000,
  })
}

export function useActiveDownloads() {
  const qc = useQueryClient()
  return useQuery({
    queryKey: downloadKeys.active(),
    queryFn: () => api.downloads.active(),
    refetchInterval: 2000,
  })
}

// For WebSocket to patch cache
export function useDownloadsCache() {
  return useQueryClient()
}
