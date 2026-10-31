import { useQuery } from '@tanstack/react-query'

export interface PulseCell { t: string; ok: number; error: number; down: number; queued: number }
export interface OverviewSub {
  id: number; name: string; live: boolean; enabled: boolean
  last_checked_at: string | null; pulse: PulseCell[]
}
export interface Arrival {
  id: number; title: string; subtitle: string | null; size_bytes: number | null
  duration_sec: number | null; at: string | null; has_thumb: boolean
}
export interface Attention {
  failed: number; needs_review: number; wanted: number
  cleanup_paused: { count: number; gb: number } | null
}
export interface Overview {
  telegram: { status: 'connected' | 'disconnected' | 'unconfigured'; last_ok_poll_at: string | null }
  subscriptions: OverviewSub[]
  recent: Arrival[]
  attention: Attention
  last_24h: { downloaded: number; bytes: number; series: { t: string; count: number; bytes: number }[] }
}

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url, { credentials: 'include' })
  if (!r.ok) throw Object.assign(new Error(`HTTP ${r.status}`), { status: r.status })
  return r.json()
}

export function useOverview(hours: number) {
  return useQuery({
    queryKey: ['overview', hours],
    queryFn: () => get<Overview>(`/api/overview?hours=${hours}`),
    refetchInterval: 30_000,
  })
}
