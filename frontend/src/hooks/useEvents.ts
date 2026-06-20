import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const eventKeys = {
  all: ['events'] as const,
  filtered: (filters: any) => [...eventKeys.all, filters] as const,
}

export function useEvents(filters?: Parameters<typeof api.events.list>[0]) {
  return useQuery({
    queryKey: eventKeys.filtered(filters || {}),
    queryFn: () => api.events.list(filters),
    refetchInterval: 5000,
  })
}
