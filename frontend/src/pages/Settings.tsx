import { useEffect, useState } from 'react'
import { Page, PageHeader } from '@/components/shared/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { useSettings } from '@/hooks/useSettings'
import { usePlugins } from '@/hooks/usePlugins'
import { GeneralSection, CleanupSection } from '@/components/settings/GeneralCleanup'
import { NotificationsSettings } from '@/components/settings/NotificationsSettings'
import { AppearanceSection } from '@/components/settings/AppearanceSection'
import { PluginsSection } from '@/components/settings/PluginsSection'
import { AccountSection } from '@/components/settings/AccountSection'
import { cn } from '@/lib/utils'

const SECTIONS = [
  ['general', 'General'], ['cleanup', 'Cleanup'], ['notifications', 'Notifications'],
  ['appearance', 'Appearance'], ['plugins', 'Plugins'], ['account', 'Account'],
] as const

function SectionNav() {
  const [active, setActive] = useState<string>(SECTIONS[0][0])
  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-10% 0px -80% 0px' },
    )
    SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el) })
    return () => io.disconnect()
  }, [])
  return (
    <nav aria-label="Settings sections" className="flex gap-1 overflow-x-auto pb-3 lg:sticky lg:top-6 lg:flex-col lg:self-start lg:pb-0">
      {SECTIONS.map(([id, label]) => (
        <a key={id} href={`#${id}`} aria-current={active === id ? 'true' : undefined}
          onClick={(e) => { e.preventDefault(); setActive(id); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }) }}
          className={cn('whitespace-nowrap rounded-md px-3 py-1.5 text-[13px] transition-colors',
            active === id ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground')}>
          {label}
        </a>
      ))}
    </nav>
  )
}

export default function Settings() {
  const { isLoading: l1 } = useSettings()
  const { isLoading: l2 } = usePlugins()
  const loading = l1 || l2

  return (
    <Page>
      <PageHeader title="Settings" description="Changes are saved per section." />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[180px_minmax(0,1fr)]">
        <SectionNav />
        {loading ? (
          <div className="space-y-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-40 w-full" />)}</div>
        ) : (
          <div className="min-w-0 space-y-4">
            <GeneralSection />
            <CleanupSection />
            <NotificationsSettings />
            <AppearanceSection />
            <PluginsSection />
            <AccountSection />
          </div>
        )}
      </div>
    </Page>
  )
}
