import { useQuery } from '@tanstack/react-query'

export interface Health {
  status: 'ok' | 'down' | 'stale'
  telegram?: 'connected' | 'disconnected' | 'unconfigured'
  last_ok_poll_at?: string | null
}

// /api/health answers 503 with a JSON body when sync is unhealthy; read it either way.
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async (): Promise<Health> => (await fetch('/api/health', { credentials: 'include' })).json(),
    refetchInterval: 30_000,
  })
}
