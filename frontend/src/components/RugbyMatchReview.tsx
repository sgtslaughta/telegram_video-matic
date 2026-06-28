import { useState } from 'react'
import { toast } from 'sonner'
import { useRugbyMatches, useLeagueFixtures, usePatchMatch, useRefreshCatalog } from '@/hooks/useRugby'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AlertCircle, RotateCw } from 'lucide-react'
import type * as T from '@/lib/types'

export function RugbyMatchReview() {
  const { data: matches, isLoading: matchesLoading } = useRugbyMatches('needs_review')
  const patchMatch = usePatchMatch()
  const refreshCatalog = useRefreshCatalog()
  const [expandedMatch, setExpandedMatch] = useState<number | null>(null)

  if (matchesLoading) return <div className="text-sm text-muted-foreground">Loading matches...</div>

  if (!matches || matches.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
        No matches awaiting review
      </div>
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">Match Review ({matches.length})</h3>
        <Button
          onClick={handleRefresh}
          disabled={refreshCatalog.isPending}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RotateCw className="h-4 w-4" />
          Refresh Leagues
        </Button>
      </div>

      <div className="space-y-3">
        {matches.map((match) => (
          <Card key={match.media_id} className="border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800">
            <CardContent className="pt-4">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1">
                    <p className="font-semibold">
                      {match.home_name} vs {match.away_name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {match.season ?? '—'}{match.round ? ` · R${match.round}` : ''}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Confidence: {Math.round((match.confidence ?? 0) * 100)}%
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-block rounded bg-amber-100 px-2 py-1 text-xs font-medium text-amber-900 dark:bg-amber-900 dark:text-amber-100">
                      needs review
                    </span>
                  </div>
                </div>

                {expandedMatch === match.media_id ? (
                  <FixtureSelector
                    match={match}
                    onSelect={(fixtureId) => handleChangeFixture(match, fixtureId)}
                    onCancel={() => setExpandedMatch(null)}
                  />
                ) : (
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleConfirm(match)}
                      disabled={patchMatch.isPending}
                      size="sm"
                      variant="default"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Confirm
                    </Button>
                    <Button
                      onClick={() => setExpandedMatch(match.media_id)}
                      disabled={patchMatch.isPending}
                      size="sm"
                      variant="outline"
                    >
                      Change Fixture
                    </Button>
                    <Button
                      onClick={() => handleReject(match)}
                      disabled={patchMatch.isPending}
                      size="sm"
                      variant="destructive"
                    >
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
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
    return <div className="text-sm text-muted-foreground">Loading fixtures...</div>
  }

  if (!fixtures || fixtures.length === 0) {
    return <div className="text-sm text-muted-foreground">No fixtures available for this season</div>
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">Select the correct fixture:</label>
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
        <Button onClick={() => onSelect(0)} disabled={false} size="sm" variant="default">
          Assign
        </Button>
        <Button onClick={onCancel} size="sm" variant="outline">
          Cancel
        </Button>
      </div>
    </div>
  )
}
