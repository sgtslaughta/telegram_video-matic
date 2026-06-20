import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const subscriptionKeys = {
  all: ['subscriptions'] as const,
  list: () => [...subscriptionKeys.all, 'list'] as const,
  detail: (id: number) => [...subscriptionKeys.all, 'detail', id] as const,
}

export function useSubscriptions() {
  return useQuery({
    queryKey: subscriptionKeys.list(),
    queryFn: () => api.subscriptions.list(),
  })
}

export function useSubscription(id: number) {
  return useQuery({
    queryKey: subscriptionKeys.detail(id),
    queryFn: () => api.subscriptions.get(id),
    enabled: id > 0,
  })
}

export function useCreateSubscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: T.SubscriptionCreate) => api.subscriptions.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: subscriptionKeys.list() })
    },
  })
}

export function useUpdateSubscription(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: T.SubscriptionUpdate) => api.subscriptions.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: subscriptionKeys.detail(id) })
      qc.invalidateQueries({ queryKey: subscriptionKeys.list() })
    },
  })
}

export function useDeleteSubscription(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.subscriptions.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: subscriptionKeys.list() })
    },
  })
}

export function useScanSubscription(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.subscriptions.scan(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: subscriptionKeys.detail(id) })
    },
  })
}
