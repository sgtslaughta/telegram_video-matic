import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const mediaKeys = {
  all: ['media'] as const,
  list: () => [...mediaKeys.all, 'list'] as const,
  listFiltered: (filters: any) => [...mediaKeys.list(), filters] as const,
  detail: (id: number) => [...mediaKeys.all, 'detail', id] as const,
}

export function useMedia(filters?: T.PaginatedResponse<T.MediaItem> extends any ? Parameters<typeof api.media.list>[0] : never) {
  return useQuery({
    queryKey: mediaKeys.listFiltered(filters || {}),
    queryFn: () => api.media.list(filters),
  })
}

export function useMediaDetail(id: number) {
  return useQuery({
    queryKey: mediaKeys.detail(id),
    queryFn: () => api.media.get(id),
    enabled: id > 0,
  })
}

export function useDownloadMedia(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.media.download(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: mediaKeys.detail(id) })
    },
  })
}

export function useRequeueMedia(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.media.requeue(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: mediaKeys.detail(id) })
    },
  })
}
