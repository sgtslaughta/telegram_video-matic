import { useQuery } from '@tanstack/react-query'
import { fetchAPI } from '@/lib/api'

export interface WantedGame {
  fixture_id: number; league: string; season: string; round: string | null
  home: string; away: string; date: string; days_missing: number
  last_searched_at: string | null; attempts: number
  state: 'missing' | 'searching' | 'not_found'; subscription_id: number
}
export interface Candidate {
  channel_id: number; tg_msg_id: number; file_name: string | null; caption: string | null
  size_bytes: number | null; date: string; confidence: number; auto: boolean
  already_tracked: boolean; media_id: number | null; media_status: string | null
}
export interface FailedDownload {
  media_id: number; file_name: string | null; caption: string | null; size_bytes: number | null
  date_posted: string; subscription_id: number | null; error: string | null
  attempt: number; last_attempt_at: string | null
}
export type HistoryKind = 'downloaded' | 'failed' | 'skipped' | 'deleted' | 'matched' | 'other'
export interface HistoryItem {
  at: string; kind: HistoryKind; media_id: number | null; file_name: string | null
  message: string; level: string
}

export const dq = {
  wanted: ['downloads', 'wanted'] as const,
  failed: ['downloads', 'failed'] as const,
  history: ['downloads', 'history'] as const,
}

/** Rugby plugin may be absent: a 404/500 resolves to null so the section hides. */
export const useWanted = () => useQuery({
  queryKey: dq.wanted,
  queryFn: () => fetchAPI<WantedGame[]>('/plugins/rugby/wanted').catch(() => null),
  refetchInterval: 30000,
})

export const useFailed = () => useQuery({
  queryKey: dq.failed,
  queryFn: () => fetchAPI<FailedDownload[]>('/wanted/failed'),
  refetchInterval: 30000,
})

export const post = <R = unknown>(path: string, body?: unknown) =>
  fetchAPI<R>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
