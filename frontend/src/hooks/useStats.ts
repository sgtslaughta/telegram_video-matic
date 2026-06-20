import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'
import { MediaStatus } from '@/lib/types'

export function useStats(): { activeSubs: number; downloaded: number; failed: number; storageBytes: number; isLoading: boolean } {
  const subs = useQuery({ queryKey: ['subscriptions', 'list'], queryFn: () => api.subscriptions.list() })
  const downloaded = useQuery({
    queryKey: ['media', 'list', { status: MediaStatus.DOWNLOADED }],
    queryFn: () => api.media.list({ status: MediaStatus.DOWNLOADED }),
  })
  const failed = useQuery({
    queryKey: ['media', 'list', { status: MediaStatus.FAILED }],
    queryFn: () => api.media.list({ status: MediaStatus.FAILED }),
  })

  return {
    activeSubs: subs.data?.filter((s) => s.enabled).length ?? 0,
    downloaded: downloaded.data?.length ?? 0,
    failed: failed.data?.length ?? 0,
    storageBytes: (downloaded.data ?? []).reduce((n, m) => n + (m.size_bytes ?? 0), 0),
    isLoading: subs.isLoading || downloaded.isLoading || failed.isLoading,
  }
}
