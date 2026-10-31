import type { ReactNode } from 'react'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import type { SubscriptionEditorState } from '@/hooks/useSubscriptionEditor'

/** Props shared by every editor section. */
export interface SectionProps {
  s: SubscriptionEditorState
  update: <K extends keyof SubscriptionEditorState>(key: K, value: SubscriptionEditorState[K]) => void
}

export function Section({ title, description, children, className }: {
  title: string; description?: string; children: ReactNode; className?: string
}) {
  return (
    <section className={cn('rounded-lg border border-border bg-card', className)}>
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-[13px] font-semibold">{title}</h2>
        {description && <p className="mt-0.5 text-[12px] text-muted-foreground">{description}</p>}
      </div>
      <div className="space-y-4 p-4">{children}</div>
    </section>
  )
}

export function Field({ label, htmlFor, hint, error, children }: {
  label: string; htmlFor?: string; hint?: string; error?: string | null; children: ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor} className="text-[13px] font-medium">{label}</Label>
      {children}
      {error
        ? <p role="alert" className="text-[12px] text-err">{error}</p>
        : hint && <p className="text-[12px] text-muted-foreground">{hint}</p>}
    </div>
  )
}

export function ToggleRow({ id, label, hint, checked, onChange }: {
  id: string; label: string; hint?: string; checked: boolean; onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0">
        <Label htmlFor={id} className="text-[13px] font-medium">{label}</Label>
        {hint && <p className="text-[12px] text-muted-foreground">{hint}</p>}
      </div>
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
    </div>
  )
}
