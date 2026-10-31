import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

/** Settings panel. The footer with "Save changes" only appears when dirty. */
export function SettingsSection({ id, title, description, dirty, saving, onSave, children }: {
  id: string; title: string; description?: ReactNode; dirty?: boolean; saving?: boolean
  onSave?: () => void; children: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-6 rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-[13px] font-semibold">{title}</h2>
        {description && <p className="mt-0.5 text-[12px] text-muted-foreground">{description}</p>}
      </div>
      <div className="space-y-5 p-4">{children}</div>
      {dirty && onSave && (
        <div className="flex justify-end border-t border-border px-4 py-2.5">
          <Button size="sm" onClick={onSave} disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</Button>
        </div>
      )}
    </section>
  )
}

export function Field({ id, label, help, children }: { id: string; label: string; help?: ReactNode; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-[13px] font-medium">{label}</Label>
      {children}
      {help && <p className="text-[12px] text-muted-foreground">{help}</p>}
    </div>
  )
}

export const inputCls = 'h-9 max-w-xs text-[13px]'
