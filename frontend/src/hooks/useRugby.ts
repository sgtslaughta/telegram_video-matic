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

export function useRugbyPreview() {
  return useMutation({
    mutationFn: (data: { leagueId: number; text: string }) =>
      api.rugby.preview(data.leagueId, data.text),
  })
}
