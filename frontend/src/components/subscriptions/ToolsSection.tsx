import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useRescan } from '@/hooks/useSubscriptionTools'
import { Section } from './Section'

function RescanDialog({ id, open, onOpenChange }: { id: number; open: boolean; onOpenChange: (o: boolean) => void }) {
  const [days, setDays] = useState('7')
  const rescan = useRescan(id)
  const n = Number(days)
  const valid = Number.isInteger(n) && n >= 1 && n <= 365
  const run = async () => {
    try {
      const r = await rescan.mutateAsync(n)
      toast.success(`Rescan found ${r.found}, queued ${r.queued}, skipped ${r.skipped}`, { duration: 6000 })
      onOpenChange(false)
    } catch (e) {
      toast.error('Rescan failed', { description: e instanceof Error ? e.message : String(e), duration: Infinity })
    }
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Rescan recent posts</DialogTitle>
          <DialogDescription>Look back through the channel and queue anything the filter now allows.</DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          <Label htmlFor="rescanDays" className="text-[13px] font-medium">Days to look back</Label>
          <Input id="rescanDays" type="number" min={1} max={365} value={days} onChange={(e) => setDays(e.target.value)} />
          {!valid && <p role="alert" className="text-[12px] text-err">Enter a number from 1 to 365.</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={run} disabled={!valid || rescan.isPending}>{rescan.isPending ? 'Rescanning…' : 'Rescan'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function ToolsSection({ id }: { id: number }) {
  const [open, setOpen] = useState(false)
  return (
    <Section title="Tools">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[13px] font-medium">Rescan recent posts</p>
          <p className="text-[12px] text-muted-foreground">Re-check history after changing the filter.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setOpen(true)}>Rescan</Button>
      </div>
      <RescanDialog id={id} open={open} onOpenChange={setOpen} />
    </Section>
  )
}
