import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'

export const downloadKeys = {
  active: () => ['downloads', 'active'] as const,
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
