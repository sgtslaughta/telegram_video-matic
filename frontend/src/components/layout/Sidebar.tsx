import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, BookOpen, Compass, DownloadCloud, ActivitySquare, Settings, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export default function Sidebar({
  connected,
  onConnectClick,
}: {
  connected: boolean
  onConnectClick: () => void
}) {
  const location = useLocation()
  const links = [
    { label: 'Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'Subscriptions', href: '/subscriptions', icon: BookOpen },
    { label: 'Browse', href: '/browse', icon: Compass },
    { label: 'Downloads', href: '/downloads', icon: DownloadCloud },
    { label: 'Activity', href: '/activity', icon: ActivitySquare },
    { label: 'Settings', href: '/settings', icon: Settings },
  ]
  const isActive = (href: string) =>
    href === '/' ? location.pathname === '/' : location.pathname.startsWith(href)

  return (
    <nav className="flex h-screen w-60 flex-col border-r border-border bg-card">
      <div className="flex h-16 items-center border-b border-border px-6">
        <h1 className="text-lg font-semibold tracking-tight">Video-Matic</h1>
      </div>
      <div className="flex-1 space-y-1 p-3">
        {links.map((link) => {
          const active = isActive(link.href)
          const Icon = link.icon
          return (
            <Link key={link.href} to={link.href}>
              <Button
                variant="ghost"
                className={cn(
                  'w-full justify-start gap-2 font-normal',
                  active && 'bg-secondary font-medium text-secondary-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {link.label}
              </Button>
            </Link>
          )
        })}
      </div>
      <div className="border-t border-border p-3">
        <Button variant="ghost" className="w-full justify-start gap-2 font-normal" onClick={onConnectClick}>
          <Send className="h-4 w-4" />
          <span className="flex-1 text-left">Telegram</span>
          <span
            className={cn(
              'h-2 w-2 rounded-full',
              connected ? 'bg-green-500' : 'bg-amber-500'
            )}
            aria-label={connected ? 'connected' : 'not connected'}
          />
        </Button>
      </div>
    </nav>
  )
}
