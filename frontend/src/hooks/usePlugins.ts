import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const pluginKeys = {
  all: () => ['plugins'] as const,
}

export function usePlugins() {
  return useQuery({
    queryKey: pluginKeys.all(),
    queryFn: () => api.plugins.list(),
    staleTime: Infinity,
  })
}

export function useUpdatePlugin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; config: T.PluginPatchRequest }) =>
      api.plugins.update(data.name, data.config),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: pluginKeys.all() })
    },
  })
}
