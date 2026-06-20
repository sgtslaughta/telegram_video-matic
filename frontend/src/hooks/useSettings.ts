import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const settingKeys = {
  all: () => ['settings'] as const,
}

export function useSettings() {
  return useQuery({
    queryKey: settingKeys.all(),
    queryFn: () => api.settings.get(),
    staleTime: Infinity,
  })
}

export function useUpdateSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: T.SettingsUpdate) => api.settings.update(data),
    onSuccess: (data) => {
      qc.setQueryData(settingKeys.all(), data)
    },
  })
}
