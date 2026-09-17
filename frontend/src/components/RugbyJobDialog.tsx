import { useEffect, useState } from 'react'
import { useRugbyJobReport, useRugbyRunJob } from '@/hooks/useRugby'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { toast } from 'sonner'
import type * as T from '@/lib/types'

const COPY: Record<T.RugbyJob, { title: string; blurb: string; apply: string }> = {
  import: {
    title: 'Import library files',
    blurb: 'Adds video files already on disk (not downloaded by TVM) and matches them. Nothing moves.',
    apply: 'Import',
  },
  rematch: {
    title: 'Re-match games',
    blurb: 'Retries unmatched games and re-scores auto matches (confirmed ones are kept), asking the API for missing fixtures. Applying files matched games.',
    apply: 'Apply matches',
  },
  reconcile: {
    title: 'Reorganize library',
    blurb: 'Moves every rugby video into its league / Season folder and rewrites Jellyfin metadata. Existing files are never overwritten.',
    apply: 'Move files',
  },
}

/** Last `n` path segments — enough to see league/Season/file. */
const tail = (p?: string | null, n = 3) => (p ? p.split('/').slice(-n).join('/') : '')

function Row({ row }: { row: T.RugbyPlanRow }) {
  const moves = row.to && row.from && row.to !== row.from
  return (
    <li className="border-b py-2 text-xs last:border-0">
      {row.file && <p className="font-medium">{row.file}</p>}
      {row.fixture && (
        <p className="text-muted-foreground">
          {row.status === 'needs_review' ? 'Review: ' : ''}{row.fixture}
          {row.previous && <span className="line-through"> (was {row.previous})</span>}
        </p>
      )}
      {row.status === 'none' && <p className="text-muted-foreground">No fixture found</p>}
      {moves ? (
        <p className="break-all">
          <span className="text-muted-foreground">{tail(row.from)}</span> → {tail(row.to)}
        </p>
      ) : row.from && row.to ? (
        <p className="text-muted-foreground">Stays in place</p>
      ) : null}
    </li>
  )
}

/** Preview-then-apply runner: opening starts a dry run and shows its plan;
 * Apply runs the job for real. */
export function RugbyJobDialog({ job, onClose }: { job: T.RugbyJob; onClose: () => void }) {
  const run = useRugbyRunJob()
  const [phase, setPhase] = useState<'preview' | 'apply'>('preview')
  const report = useRugbyJobReport(job, true)
  const rep = report.data

  // Mounted per job (keyed by the parent), so this runs once per open.
  useEffect(() => {
    run.mutate({ job, dryRun: true }, {
      // 409: already running (e.g. reopened) — just keep showing its progress.
      onError: (e) => {
        const msg = e instanceof Error ? e.message : 'Could not start preview'
        if (!msg.includes('already running')) toast.error(msg)
      },
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job])

  const copy = COPY[job]
  const running = run.isPending || !rep || rep.running
  const ready = !running && (!!rep?.error || rep?.dry_run === (phase === 'preview'))
  const rows = rep?.plan ?? []
  const files = rep?.files ?? []
  const conflicts = rep?.conflicts ?? []

  const apply = () => {
    setPhase('apply')
    run.mutate({ job, dryRun: false }, {
      onError: (e) => toast.error(e instanceof Error ? e.message : 'Could not start job'),
    })
  }

  const summary = ready && rep
    ? Object.entries(rep)
        .filter(([k, v]) => typeof v === 'number' && !['done', 'total'].includes(k))
        .map(([k, v]) => `${k.replace('_', ' ')}: ${v}`)
        .join(' · ')
    : ''

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{copy.title}{phase === 'preview' ? ' — preview' : ''}</DialogTitle>
          <DialogDescription>{copy.blurb}</DialogDescription>
        </DialogHeader>

        {running || !ready ? (
          <div className="space-y-2 py-4 text-sm">
            <p>{phase === 'preview' ? 'Building plan…' : 'Applying…'}{' '}
              {rep?.total ? `${rep.done} / ${rep.total}` : ''}</p>
            {!!rep?.total && <ProgressBar progress={((rep.done ?? 0) / rep.total) * 100} />}
            <p className="text-xs text-muted-foreground">
              API lookups are rate limited; large libraries take a while. You can close this — the job keeps running.
            </p>
          </div>
        ) : rep?.error ? (
          <p className="py-4 text-sm text-red-600">Failed: {rep.error}</p>
        ) : (
          <div className="space-y-2">
            <p className="text-sm">{summary}</p>
            {conflicts.length > 0 && (
              <p className="text-sm text-amber-600">
                {conflicts.length} file(s) skipped: destination already exists (duplicates).
              </p>
            )}
            <ul className="max-h-[50vh] overflow-y-auto rounded border px-3">
              {rows.map((r) => <Row key={`${r.media_id}-${r.to}`} row={r} />)}
              {files.map((f) => <li key={f} className="border-b py-2 text-xs last:border-0">{f}</li>)}
              {rows.length + files.length === 0 && (
                <li className="py-4 text-center text-sm text-muted-foreground">Nothing to do</li>
              )}
            </ul>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>{phase === 'apply' && ready ? 'Done' : 'Cancel'}</Button>
          {phase === 'preview' && (
            <Button onClick={apply} disabled={!ready || !!rep?.error || rows.length + files.length === 0}>
              {copy.apply}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
