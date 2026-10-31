import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Panel({ title, aside, children, className, id }: {
  title: string; aside?: ReactNode; children: ReactNode; className?: string; id?: string
}) {
  return (
    <section id={id} className={cn('min-w-0 rounded-lg border border-border bg-card', className)}>
      <div className="flex h-11 items-center justify-between border-b border-border px-4">
        <h2 className="text-[13px] font-semibold">{title}</h2>
        {aside && <span className="text-[12px] text-muted-foreground">{aside}</span>}
      </div>
      {children}
    </section>
  )
}

export const TH = 'h-9 px-4 text-left text-[12px] font-normal text-muted-foreground'
export const TD = 'h-10 px-4'
