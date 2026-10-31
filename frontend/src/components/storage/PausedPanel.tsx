import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { usePruneConfirm } from '@/hooks/useStorage'
import { withToast } from '@/lib/toast'
import { DestructiveConfirm } from './DestructiveConfirm'

export function PausedPanel({ count, gb, onReview }: { count: number; gb: number; onReview: () => void }) {
  const [open, setOpen] = useState(false)
  const prune = usePruneConfirm()
  const noun = `${count} file${count === 1 ? '' : 's'}`
  const run = async () => {
    setOpen(false)
    await withToast(() => prune.mutateAsync(), { success: `Deleted ${noun}` })
  }
  return (
    <section className="flex flex-wrap items-center gap-4 rounded-lg border border-warn/40 bg-warn/10 p-4">
      <AlertTriangle className="h-5 w-5 shrink-0 text-warn" strokeWidth={1.75} />
      <div className="min-w-0 flex-1">
        <h2 className="text-[13px] font-semibold">Cleanup is paused: {noun} ({gb} GB) would be deleted</h2>
        <p className="text-[12px] text-muted-foreground">Nothing is removed until you approve it.</p>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={onReview}>Review list</Button>
        <Button variant="destructive" size="sm" disabled={prune.isPending} onClick={() => setOpen(true)}>Delete {noun}</Button>
      </div>
      <DestructiveConfirm open={open} title={`Delete ${noun}?`}
        description={`This permanently deletes ${noun} (${gb} GB) from disk. It can’t be undone.`}
        confirmText={`Delete ${noun}`} onConfirm={run} onCancel={() => setOpen(false)} />
    </section>
  )
}
