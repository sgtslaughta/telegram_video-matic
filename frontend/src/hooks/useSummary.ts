import { useQuery } from '@tanstack/react-query'
import { fetchAPI } from '@/lib/api'
import type { Arrival, Attention } from './useOverview'

export interface Incident { kind: 'telegram_down'; started: string; ended: string | null; hours: number }
export interface Summary {
  since: string
  show: boolean
  incidents: Incident[]
  arrivals: { group: string; items: Arrival[] }[]
  attention: Attention
  stats: { downloaded: number; bytes: number }
}

export function useSummary() {
  return useQuery({ queryKey: ['summary'], queryFn: () => fetchAPI<Summary>('/summary'), staleTime: Infinity })
}

export const markSeen = () => fetchAPI('/summary/seen', { method: 'POST' })
