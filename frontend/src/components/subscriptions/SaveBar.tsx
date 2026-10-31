import { Button } from '@/components/ui/button'

/** Sticky footer, only rendered while the form has unsaved changes. */
export function SaveBar({ onSave, onDiscard, saving, label }: { onSave: () => void; onDiscard: () => void; saving: boolean; label: string }) {
  return (
    <div role="region" aria-label="Unsaved changes"
      className="sticky bottom-4 z-30 mt-6 flex h-12 items-center justify-between gap-3 rounded-lg border border-border bg-card px-4">
      <p className="text-[13px] text-muted-foreground">You have unsaved changes.</p>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={onDiscard} disabled={saving}>Discard</Button>
        <Button size="sm" onClick={onSave} disabled={saving}>{saving ? 'Saving…' : label}</Button>
      </div>
    </div>
  )
}
