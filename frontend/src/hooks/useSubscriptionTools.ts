import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { fetchAPI } from '@/lib/api'

export interface PreviewParams {
  channel_id: number
  topic_id?: number | null
  filter_regex?: string
  filter_mode: 'include' | 'exclude'
  min_size_mb?: number | null
  max_size_mb?: number | null
  date_from?: string | null
  date_to?: string | null
  schedule_days?: string[]
}

export interface PreviewItem {
  tg_msg_id: number
  file_name: string | null
  caption: string | null
  size_bytes: number | null
  date_posted: string
  would: 'download' | 'skip'
  reason: string
}

export interface RescanResult { found: number; queued: number; skipped: number }

export function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

/** Live filter preview. Pass null to disable; requests are debounced 600ms. */
export function useFilterPreview(params: PreviewParams | null) {
  const key = useDebounced(params ? JSON.stringify(params) : null, 600)
  return useQuery({
    queryKey: ['filter-preview', key],
    queryFn: () => fetchAPI<PreviewItem[]>('/subscriptions/preview-filter', { method: 'POST', body: key! }),
    enabled: key !== null,
    retry: false,
    staleTime: 30_000,
  })
}

export function useRescan(id: number) {
  return useMutation({
    mutationFn: (days: number) =>
      fetchAPI<RescanResult>(`/subscriptions/${id}/rescan`, { method: 'POST', body: JSON.stringify({ days }) }),
  })
}
