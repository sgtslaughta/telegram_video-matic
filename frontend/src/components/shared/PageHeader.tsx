import type { ReactNode } from 'react'

/** Page title row: title + optional one-line description, actions right-aligned. */
export function PageHeader({ title, description, actions }: { title: string; description?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3 pb-5">
      <div className="min-w-0">
        <h1 className="text-[20px] font-semibold leading-7 tracking-tight">{title}</h1>
        {description && <p className="mt-0.5 text-[13px] text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  )
}

/** Standard page body width + padding (bottom pad clears the mobile nav). */
export function Page({ children, wide }: { children: ReactNode; wide?: boolean }) {
  return <div className={`mx-auto w-full px-5 pb-24 pt-6 md:px-8 md:pb-10 ${wide ? 'max-w-[1400px]' : 'max-w-[1100px]'}`}>{children}</div>
}
