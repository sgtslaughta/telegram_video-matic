import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'
import type * as T from '@/lib/types'

export const rugbyKeys = {
  status: () => ['rugby', 'status'] as const,
  leagues: () => ['rugby', 'leagues'] as const,
  fixtures: (leagueId: number, season: string) => ['rugby', 'fixtures', leagueId, season] as const,
  matches: (status?: string) => ['rugby', 'matches', status] as const,
  enrichment: (channelId: number) => ['rugby', 'enrichment', channelId] as const,
}

export function useRugbyStatus() {
  return useQuery({
    queryKey: rugbyKeys.status(),
    queryFn: () => api.rugby.status(),
    staleTime: 30 * 1000,
    // Poll quickly while a metadata sync is running so the progress bar moves.
    refetchInterval: (q) => {
      const s = q.state.data?.status as Record<string, unknown> | undefined
      return s?.syncing ? 1500 : false
    },
  })
}

export function useRugbyLeagues() {
  return useQuery({
    queryKey: rugbyKeys.leagues(),
    queryFn: () => api.rugby.leagues(),
    staleTime: 60 * 1000,
  })
}

export function useLeagueFixtures(leagueId: number, season: string) {
  return useQuery({
    queryKey: rugbyKeys.fixtures(leagueId, season),
    queryFn: () => api.rugby.fixtures(leagueId, season),
    enabled: !!leagueId,
    staleTime: 60 * 1000,
  })
}

export function useRugbyMatches(status?: string) {
  return useQuery({
    queryKey: rugbyKeys.matches(status),
    queryFn: () => api.rugby.matches(status),
    staleTime: 30 * 1000,
  })
}

export function useRefreshCatalog() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.rugby.refreshCatalog(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rugbyKeys.leagues() })
      qc.invalidateQueries({ queryKey: rugbyKeys.status() })
    },
  })
}

export function useRefreshLeague() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (leagueId: number) => api.rugby.refreshLeague(leagueId),
    onSuccess: (_, leagueId) => {
      qc.invalidateQueries({ queryKey: rugbyKeys.status() })
      // Invalidate all fixture queries for this league across all seasons
      qc.invalidateQueries({ queryKey: ['rugby', 'fixtures', leagueId] })
    },
  })
}

export function usePatchMatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { mediaId: number; status?: string; fixture_id?: number }) =>
      api.rugby.patchMatch(data.mediaId, { status: data.status, fixture_id: data.fixture_id }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rugbyKeys.matches() })
    },
  })
}

export function useSubscriptionLeague(subId: number | null) {
  return useQuery({
    queryKey: ['rugby', 'sub-league', subId] as const,
    queryFn: () => api.rugby.getSubscriptionLeague(subId as number),
    enabled: !!subId,
  })
}

export function useSetSubscriptionLeague() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { subId: number; leagueId: number | null }) =>
      api.rugby.setSubscriptionLeague(data.subId, data.leagueId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rugbyKeys.leagues() })
    },
  })
}

export function useRugbyEnrichment(channelId: number | null) {
  return useQuery({
    queryKey: rugbyKeys.enrichment(channelId ?? 0),
    queryFn: () => api.rugby.enrichment(channelId!),
    enabled: !!channelId,
    staleTime: 60 * 1000,
  })
}

export function useRugbyRescan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.rugby.rescan(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plugins'] })
      qc.invalidateQueries({ queryKey: rugbyKeys.status() })
    },
  })
}

/** Last report of a rugby maintenance job; polls every 2s while it runs.
 * 404 (never run) resolves to null. */
export function useRugbyJobReport(job: T.RugbyJob | null, enabled: boolean) {
  return useQuery({
    queryKey: ['rugby', 'report', job],
    queryFn: () => api.rugby.report(job!).catch(() => null),
    enabled: enabled && !!job,
    refetchInterval: (q) => (q.state.data?.running ? 2000 : false),
  })
}

/** Start import / rematch / reconcile, as a dry run (plan only) or for real. */
export function useRugbyRunJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { job: T.RugbyJob; dryRun: boolean }) => api.rugby.runJob(v.job, v.dryRun),
    // Returned promise keeps the mutation pending until the report refetch
    // lands, so the dialog never flashes the previous run's plan.
    onSuccess: (_d, v) => {
      if (!v.dryRun) {
        qc.invalidateQueries({ queryKey: rugbyKeys.status() })
        qc.invalidateQueries({ queryKey: ['rugby', 'matches'] })
      }
      return qc.invalidateQueries({ queryKey: ['rugby', 'report', v.job] })
    },
  })
}

type BrowseLike = { tg_msg_id: number; caption?: string | null; file_name?: string | null; date_posted?: string | null }

/** Enrich the live browse items currently on screen (works for un-cached
 * videos in any topic). Refetches only when the visible id-set changes. */
export function useRugbyEnrichMessages(items: BrowseLike[]) {
  const messages = items.map((i) => ({
    tg_msg_id: i.tg_msg_id,
    text: i.caption || i.file_name || '',
    date: i.date_posted ?? null,
  }))
  const key = messages.map((m) => m.tg_msg_id).sort((a, b) => a - b).join(',')
  return useQuery({
    queryKey: ['rugby', 'enrich-messages', key],
    queryFn: () => api.rugby.enrichMessages(messages),
    enabled: messages.length > 0,
    staleTime: 30 * 1000,
  })
}

export function useRugbyEnrichmentByMedia(mediaIds: number[]) {
  const key = mediaIds.slice().sort((a, b) => a - b).join(',')
  return useQuery({
    queryKey: ['rugby', 'enrichment-by-media', key],
    queryFn: () => api.rugby.enrichmentByMedia(mediaIds),
    enabled: mediaIds.length > 0,
    staleTime: 60 * 1000,
  })
}

export function useRugbyPreview() {
  return useMutation({
    mutationFn: (data: { leagueId: number; text: string }) =>
      api.rugby.preview(data.leagueId, data.text),
  })
}
