import {
  LayoutGrid, Rss, Compass, ArrowDownToLine, History, HardDrive, Settings, type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  label: string
  href: string
  icon: LucideIcon
  keys: string // "g o" style shortcut, second key
}

export const NAV: NavItem[] = [
  { label: 'Overview', href: '/', icon: LayoutGrid, keys: 'o' },
  { label: 'Subscriptions', href: '/subscriptions', icon: Rss, keys: 's' },
  { label: 'Downloads', href: '/downloads', icon: ArrowDownToLine, keys: 'd' },
  { label: 'Browse', href: '/browse', icon: Compass, keys: 'b' },
  { label: 'Activity', href: '/activity', icon: History, keys: 'a' },
  { label: 'Storage', href: '/storage', icon: HardDrive, keys: 't' },
  { label: 'Settings', href: '/settings', icon: Settings, keys: ',' },
]

export const isActive = (pathname: string, href: string) =>
  href === '/' ? pathname === '/' : pathname.startsWith(href)
