import { useState } from 'react'
import { toast } from 'sonner'
import { useRugbyMatches, useLeagueFixtures, usePatchMatch, useRefreshCatalog } from '@/hooks/useRugby'
import { Skeleton } from '@/components/ui/skeleton'
import { absTime, relTime } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RotateCw } from 'lucide-react'
import type * as T from '@/lib/types'

export function RugbyMatchReview() {
  const { data: matches, isLoading: matchesLoading } = useRugbyMatches('needs_review')
  const patchMatch = usePatchMatch()
  const refreshCatalog = useRefreshCatalog()
  const [expandedMatch, setExpandedMatch] = useState<number | null>(null)

  if (matchesLoading) return <div className="space-y-2">{[0, 1].map((i) => <Skeleton key={i} className="h-24 w-full" />)}</div>

  if (!matches || matches.length === 0) {
    return (
      <p className="rounded-lg border border-border bg-card px-4 py-8 text-center text-[13px] text-muted-foreground">
        Nothing to review. Videos with an uncertain match appear here.
      </p>
    )
  }

  const handleConfirm = (match: T.RugbyMatch) => {
    patchMatch.mutate(
      { mediaId: match.media_id, status: 'confirmed' },
      {
        onSuccess: () => toast.success('Match confirmed'),
        onError: (e) => toast.error((e as Error).message),
      }
    )
  }

  const handleReject = (match: T.RugbyMatch) => {
    patchMatch.mutate(
      { mediaId: match.media_id, status: 'rejected' },
      {
        onSuccess: () => toast.success('Match rejected'),
        onError: (e) => toast.error((e as Error).message),
      }
    )
  }

  const handleChangeFixture = (match: T.RugbyMatch, fixtureId: number) => {
    patchMatch.mutate(
      { mediaId: match.media_id, fixture_id: fixtureId, status: 'confirmed' },
      {
        onSuccess: () => toast.success('Match reassigned'),
        onError: (e) => toast.error((e as Error).message),
      }
    )
    setExpandedMatch(null)
  }

  const handleRefresh = () => {
    refreshCatalog.mutate(undefined, {
      onSuccess: () => toast.success('Refresh scheduled'),
      onError: (e) => toast.error((e as Error).message),
    })
  }

  return (
    <section className="rounded-lg border border-border bg-card">
      <div className="flex h-11 items-center justify-between border-b border-border px-4">
        <h2 className="text-[13px] font-semibold">Match review <span className="font-normal text-muted-foreground">{matches.length}</span></h2>
        <Button onClick={handleRefresh} disabled={refreshCatalog.isPending} variant="outline" size="sm" className="h-7 gap-1.5 px-2 text-[12px]">
          <RotateCw className="h-3.5 w-3.5" />
          Refresh leagues
        </Button>
      </div>
      <ul className="divide-y divide-border">
        {matches.map((match) => (
          <li key={match.media_id} className="space-y-3 px-4 py-3 text-[13px]">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="min-w-0 space-y-0.5 rounded-md bg-muted/50 p-3">
                <p className="text-[12px] text-muted-foreground">Source video</p>
                <p className="break-words font-medium" title={match.source_name ?? undefined}>{match.source_name || match.source_caption || '-'}</p>
                {match.source_caption && match.source_name && <p className="line-clamp-2 text-[12px] text-muted-foreground">{match.source_caption}</p>}
                {match.source_date && <p className="text-[12px] text-muted-foreground" title={absTime(match.source_date)}>Posted {relTime(match.source_date)}</p>}
              </div>
              <div className="min-w-0 space-y-0.5 rounded-md bg-muted/50 p-3">
                <p className="text-[12px] text-muted-foreground">Suggested match, {Math.round((match.confidence ?? 0) * 100)}% confident</p>
                <p className="font-medium">{match.home_name} vs {match.away_name}</p>
                <p className="text-[12px] text-muted-foreground">{match.season ?? '-'}{match.round ? `, round ${match.round}` : ''}</p>
              </div>
            </div>
            {expandedMatch === match.media_id ? (
              <FixtureSelector match={match} onSelect={(id) => handleChangeFixture(match, id)} onCancel={() => setExpandedMatch(null)} />
            ) : (
              <div className="flex gap-2">
                <Button onClick={() => handleConfirm(match)} disabled={patchMatch.isPending} size="sm" className="h-8">Confirm match</Button>
                <Button onClick={() => setExpandedMatch(match.media_id)} disabled={patchMatch.isPending} size="sm" variant="outline" className="h-8">Change fixture</Button>
                <Button onClick={() => handleReject(match)} disabled={patchMatch.isPending} size="sm" variant="ghost" className="h-8 hover:text-err">Reject match</Button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

function FixtureSelector({
  match,
  onSelect,
  onCancel,
}: {
  match: T.RugbyMatch
  onSelect: (fixtureId: number) => void
  onCancel: () => void
}) {
  const { data: fixtures, isLoading } = useLeagueFixtures(match.league_id, match.season)

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading fixtures…</div>
  }

  if (!fixtures || fixtures.length === 0) {
    return <div className="text-[13px] text-muted-foreground">No fixtures available for this season</div>
  }

  return (
    <div className="space-y-2">
      <p className="text-[12px] text-muted-foreground">Select the correct fixture</p>
      <Select onValueChange={(val) => onSelect(parseInt(val))}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Choose a fixture..." />
        </SelectTrigger>
        <SelectContent>
          {fixtures.map((fix) => (
            <SelectItem key={fix.id} value={fix.id.toString()}>
              {fix.home_name} vs {fix.away_name} (R{fix.round})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="flex gap-2">
        <Button onClick={onCancel} size="sm" variant="outline">
          Cancel
        </Button>
      </div>
    </div>
  )
}
