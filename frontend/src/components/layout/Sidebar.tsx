import { Link, useLocation } from 'react-router-dom'
import { Moon, Sun, LogOut, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import Logo from '@/components/Logo'
import { useTheme } from '@/hooks/useTheme'
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads'
import * as api from '@/lib/api'
import { NAV, isActive } from './nav'

export default function Sidebar({
  connected,
  onConnectClick,
  onSearch,
}: {
  connected: boolean
  onConnectClick: () => void
  onSearch: () => void
}) {
  const { pathname } = useLocation()
  const { toggleTheme, effectiveTheme } = useTheme()
  const { data: active } = useActiveDownloads()
  const { data: queued } = useQueuedDownloads()
  const dlCount = (active?.length ?? 0) + (queued?.length ?? 0)

  const logout = async () => {
    await api.auth.logout().catch(() => {})
    window.location.href = '/login'
  }

  return (
    <nav
      aria-label="Main"
      className="hidden w-56 shrink-0 flex-col border-r border-border bg-card md:flex"
    >
      <div className="flex h-12 items-center gap-2 px-4">
        <Logo className="h-7 w-7" />
        <span className="text-[13px] font-semibold tracking-tight">Video-matic</span>
      </div>

      <button
        onClick={onSearch}
        className="mx-3 mb-2 flex h-8 items-center gap-2 rounded-md border border-border bg-background px-2.5 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="flex-1 text-left">Search</span>
        <kbd className="rounded border border-border px-1 text-[11px]">⌘K</kbd>
      </button>

      <ul className="flex-1 space-y-px px-2">
        {NAV.map(({ label, href, icon: Icon }) => {
          const on = isActive(pathname, href)
          return (
            <li key={href}>
              <Link
                to={href}
                aria-current={on ? 'page' : undefined}
                className={cn(
                  'relative flex h-8 items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors',
                  on ? 'bg-brand/10 font-medium text-foreground' : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground',
                )}
              >
                {on && <span aria-hidden className="absolute -left-2 top-1.5 bottom-1.5 w-[3px] rounded-r bg-brand" />}
                <Icon className={cn('h-4 w-4', on && 'text-brand')} strokeWidth={1.75} />
                <span className="flex-1">{label}</span>
                {href === '/downloads' && dlCount > 0 && (
                  <span className="rounded-full bg-brand/15 px-1.5 text-[11px] font-medium tabular-nums text-brand">{dlCount}</span>
                )}
              </Link>
            </li>
          )
        })}
      </ul>

      <div className="space-y-px border-t border-border p-2">
        <button
          onClick={onConnectClick}
          className="flex h-8 w-full items-center gap-2.5 rounded-md px-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground"
        >
          <span className={cn('h-2 w-2 rounded-full', connected ? 'bg-ok' : 'bg-err')} />
          <span className="flex-1 text-left">{connected ? 'Telegram connected' : 'Telegram offline'}</span>
        </button>
        <div className="flex gap-px">
          <button
            onClick={toggleTheme}
            aria-label={effectiveTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            className="flex h-8 flex-1 items-center gap-2.5 rounded-md px-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground"
          >
            {effectiveTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            Theme
          </button>
          <button
            onClick={logout}
            aria-label="Log out"
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  )
}

export function MobileNav() {
  const { pathname } = useLocation()
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-card md:hidden">
      {NAV.slice(0, 5).map(({ label, href, icon: Icon }) => {
        const on = isActive(pathname, href)
        return (
          <Link
            key={href}
            to={href}
            aria-current={on ? 'page' : undefined}
            className={cn('flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px]',
              on ? 'font-medium text-brand' : 'text-muted-foreground')}
          >
            <Icon className="h-5 w-5" strokeWidth={1.75} />
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
