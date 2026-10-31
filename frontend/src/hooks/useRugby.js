import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const rugbyKeys = {
    status: () => ['rugby', 'status'],
    leagues: () => ['rugby', 'leagues'],
    fixtures: (leagueId, season) => ['rugby', 'fixtures', leagueId, season],
    matches: (status) => ['rugby', 'matches', status],
    enrichment: (channelId) => ['rugby', 'enrichment', channelId],
};
export function useRugbyStatus() {
    return useQuery({
        queryKey: rugbyKeys.status(),
        queryFn: () => api.rugby.status(),
        staleTime: 30 * 1000,
        // Poll quickly while a metadata sync is running so the progress bar moves.
        refetchInterval: (q) => {
            const s = q.state.data?.status;
            return s?.syncing ? 1500 : false;
        },
    });
}
export function useRugbyLeagues() {
    return useQuery({
        queryKey: rugbyKeys.leagues(),
        queryFn: () => api.rugby.leagues(),
        staleTime: 60 * 1000,
    });
}
export function useLeagueFixtures(leagueId, season) {
    return useQuery({
        queryKey: rugbyKeys.fixtures(leagueId, season),
        queryFn: () => api.rugby.fixtures(leagueId, season),
        enabled: !!leagueId,
        staleTime: 60 * 1000,
    });
}
export function useRugbyMatches(status) {
    return useQuery({
        queryKey: rugbyKeys.matches(status),
        queryFn: () => api.rugby.matches(status),
        staleTime: 30 * 1000,
    });
}
export function useRefreshCatalog() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => api.rugby.refreshCatalog(),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: rugbyKeys.leagues() });
            qc.invalidateQueries({ queryKey: rugbyKeys.status() });
        },
    });
}
export function useRefreshLeague() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (leagueId) => api.rugby.refreshLeague(leagueId),
        onSuccess: (_, leagueId) => {
            qc.invalidateQueries({ queryKey: rugbyKeys.status() });
            // Invalidate all fixture queries for this league across all seasons
            qc.invalidateQueries({ queryKey: ['rugby', 'fixtures', leagueId] });
        },
    });
}
export function usePatchMatch() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data) => api.rugby.patchMatch(data.mediaId, { status: data.status, fixture_id: data.fixture_id }),
        onSuccess: () => {
            // Prefix key: matches() would end in `undefined`, which never equals 'needs_review'.
            qc.invalidateQueries({ queryKey: ['rugby', 'matches'] });
            qc.invalidateQueries({ queryKey: rugbyKeys.status() });
        },
    });
}
export function useSubscriptionLeague(subId) {
    return useQuery({
        queryKey: ['rugby', 'sub-league', subId],
        queryFn: () => api.rugby.getSubscriptionLeague(subId),
        enabled: !!subId,
    });
}
export function useSetSubscriptionLeague() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data) => api.rugby.setSubscriptionLeagues(data.subId, data.leagueIds),
        onSuccess: (_d, v) => {
            qc.invalidateQueries({ queryKey: rugbyKeys.leagues() });
            qc.invalidateQueries({ queryKey: ['rugby', 'sub-league', v.subId] });
        },
    });
}
export function useRugbyEnrichment(channelId) {
    return useQuery({
        queryKey: rugbyKeys.enrichment(channelId ?? 0),
        queryFn: () => api.rugby.enrichment(channelId),
        enabled: !!channelId,
        staleTime: 60 * 1000,
    });
}
export function useRugbyRescan() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => api.rugby.rescan(),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['plugins'] });
            qc.invalidateQueries({ queryKey: rugbyKeys.status() });
        },
    });
}
/** Last report of a rugby maintenance job; polls every 2s while it runs.
 * 404 (never run) resolves to null. */
export function useRugbyJobReport(job, enabled) {
    return useQuery({
        queryKey: ['rugby', 'report', job],
        queryFn: () => api.rugby.report(job).catch(() => null),
        enabled: enabled && !!job,
        refetchInterval: (q) => (q.state.data?.running ? 2000 : false),
    });
}
/** Start import / rematch / reconcile, as a dry run (plan only) or for real. */
export function useRugbyRunJob() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (v) => api.rugby.runJob(v.job, v.dryRun),
        // Returned promise keeps the mutation pending until the report refetch
        // lands, so the dialog never flashes the previous run's plan.
        onSuccess: (_d, v) => {
            if (!v.dryRun) {
                qc.invalidateQueries({ queryKey: rugbyKeys.status() });
                qc.invalidateQueries({ queryKey: ['rugby', 'matches'] });
            }
            return qc.invalidateQueries({ queryKey: ['rugby', 'report', v.job] });
        },
    });
}
/** Enrich the live browse items currently on screen (works for un-cached
 * videos in any topic). Refetches only when the visible id-set changes. */
export function useRugbyEnrichMessages(items) {
    const messages = items.map((i) => ({
        tg_msg_id: i.tg_msg_id,
        text: i.caption || i.file_name || '',
        date: i.date_posted ?? null,
    }));
    const key = messages.map((m) => m.tg_msg_id).sort((a, b) => a - b).join(',');
    return useQuery({
        queryKey: ['rugby', 'enrich-messages', key],
        queryFn: () => api.rugby.enrichMessages(messages),
        enabled: messages.length > 0,
        staleTime: 30 * 1000,
    });
}
export function useRugbyEnrichmentByMedia(mediaIds) {
    const key = mediaIds.slice().sort((a, b) => a - b).join(',');
    return useQuery({
        queryKey: ['rugby', 'enrichment-by-media', key],
        queryFn: () => api.rugby.enrichmentByMedia(mediaIds),
        enabled: mediaIds.length > 0,
        staleTime: 60 * 1000,
    });
}
export function useRugbyPreview() {
    return useMutation({
        mutationFn: (data) => api.rugby.preview(data.leagueId, data.text),
    });
}
