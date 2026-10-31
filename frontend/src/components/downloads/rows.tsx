import type { KeyboardEvent, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

/** Focusable row; Enter opens the media page when `to` is set. */
export function Row({ to, selected, className, children }: { to?: string; selected?: boolean; className?: string; children: ReactNode }) {
  const nav = useNavigate()
  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (e.key === 'Enter' && to && e.target === e.currentTarget) nav(to)
  }
  return (
    <div role="row" data-row tabIndex={0} onKeyDown={onKeyDown}
      className={cn('grid items-center gap-x-3 border-t border-border px-4 text-[13px] outline-none transition-colors first:border-t-0 hover:bg-accent/60 focus-visible:bg-accent/60 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-brand', selected && 'bg-brand/10', className)}>
      {children}
    </div>
  )
}

export function Section({ title, aside, children }: { title: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="mb-4 min-w-0 rounded-lg border border-border bg-card">
      <div className="flex h-11 items-center justify-between gap-2 border-b border-border px-4">
        <h2 className="text-[13px] font-semibold">{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  )
}

export const Empty = ({ children }: { children: ReactNode }) => (
  <p className="px-4 py-8 text-center text-[13px] text-muted-foreground">{children}</p>
)

export const RowSkeleton = ({ n = 4 }: { n?: number }) => (
  <div className="space-y-px">{Array.from({ length: n }, (_, i) => <div key={i} className="flex h-10 items-center px-4"><Skeleton className="h-4 w-full" /></div>)}</div>
)

export function Dot({ tone }: { tone: 'ok' | 'warn' | 'err' | 'muted' }) {
  return <span className={cn('inline-block h-2 w-2 shrink-0 rounded-full', { ok: 'bg-ok', warn: 'bg-warn', err: 'bg-err', muted: 'bg-muted-foreground/40' }[tone])} />
}

export function Bar({ value }: { value: number }) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-full min-w-10 overflow-hidden rounded-full bg-muted" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-brand" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-9 shrink-0 text-right text-[12px] tabular-nums text-muted-foreground">{pct}%</span>
    </div>
  )
}
