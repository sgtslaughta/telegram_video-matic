import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { absTime, formatBytes, relTime } from '@/lib/format'
import { withToast } from '@/lib/toast'
import { post, type Candidate, type WantedGame, dq } from './data'
import { Bar, Empty } from './rows'

export function SearchDialog({ game, onClose }: { game: WantedGame | null; onClose: () => void }) {
  return (
    <Dialog open={!!game} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl">{game && <Body key={game.fixture_id} game={game} />}</DialogContent>
    </Dialog>
  )
}

function Body({ game }: { game: WantedGame }) {
  const qc = useQueryClient()
  const [rows, setRows] = useState<Candidate[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [grabbed, setGrabbed] = useState<Set<string>>(new Set())

  useEffect(() => {
    let live = true
    post<Candidate[]>(`/plugins/rugby/wanted/${game.fixture_id}/search?subscription_id=${game.subscription_id}`)
      .then((r) => live && setRows(r))
      .catch((e: Error & { status?: number }) => live && setError(e.status === 503 ? 'Telegram is not connected' : e.message))
      .finally(() => qc.invalidateQueries({ queryKey: dq.wanted }))
    return () => { live = false }
  }, [game, qc])

  const grab = (c: Candidate) => withToast(async () => {
    await post(`/plugins/rugby/wanted/${game.fixture_id}/grab`, { channel_id: c.channel_id, tg_msg_id: c.tg_msg_id })
    setGrabbed((s) => new Set(s).add(`${c.channel_id}:${c.tg_msg_id}`))
    qc.invalidateQueries({ queryKey: ['downloads'] })
  }, { success: 'Download queued' })

  return (
    <>
        <DialogHeader>
          <DialogTitle>{game.home} vs {game.away}</DialogTitle>
          <DialogDescription>Matching videos found in your channels. Grab the one you want.</DialogDescription>
        </DialogHeader>
        <div className="max-h-[60vh] overflow-y-auto rounded-md border border-border">
          {error ? <Empty>{error}</Empty>
            : rows === null ? <div className="space-y-2 p-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
            : rows.length === 0 ? <Empty>No matching videos found. The search repeats automatically.</Empty>
            : (
              <table className="w-full text-[13px]">
                <thead className="text-left text-[12px] text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="px-3 py-2 font-normal">File</th>
                    <th className="hidden w-32 px-3 py-2 font-normal sm:table-cell">Match</th>
                    <th className="hidden px-3 py-2 text-right font-normal sm:table-cell">Size</th>
                    <th className="hidden px-3 py-2 font-normal md:table-cell">Posted</th>
                    <th className="w-20" />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((c) => {
                    const key = `${c.channel_id}:${c.tg_msg_id}`
                    const done = grabbed.has(key) || c.already_tracked
                    return (
                      <tr key={key} className="h-10 border-b border-border last:border-0 hover:bg-accent/60">
                        <td className="max-w-0 px-3">
                          <p className="truncate" title={c.file_name ?? c.caption ?? undefined}>{c.file_name || c.caption || `Message ${c.tg_msg_id}`}</p>
                          {c.auto && <p className="text-[12px] text-muted-foreground">Auto-grab candidate</p>}
                        </td>
                        <td className="hidden px-3 sm:table-cell"><Bar value={c.confidence} /></td>
                        <td className="hidden px-3 text-right tabular-nums text-muted-foreground sm:table-cell">{formatBytes(c.size_bytes)}</td>
                        <td className="hidden whitespace-nowrap px-3 text-muted-foreground md:table-cell" title={absTime(c.date)}>{relTime(c.date)}</td>
                        <td className="px-3 text-right">
                          <Button size="sm" variant={done ? 'ghost' : 'outline'} className="h-7 px-2 text-[12px]" disabled={done} onClick={() => grab(c)}>
                            {done ? 'Queued' : 'Grab'}
                          </Button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
        </div>
    </>
  )
}
