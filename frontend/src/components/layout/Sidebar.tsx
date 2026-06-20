import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LayoutDashboard, BookOpen, Compass, ActivitySquare, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'

export default function Sidebar() {
  const location = useLocation()
  const links = [
    { label: 'Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'Subscriptions', href: '/subscriptions', icon: BookOpen },
    { label: 'Browse', href: '/browse', icon: Compass },
    { label: 'Activity', href: '/activity', icon: ActivitySquare },
    { label: 'Settings', href: '/settings', icon: Settings },
  ]

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(href)
  }

  return (
    <nav className="w-64 h-screen bg-slate-900 text-white overflow-y-auto flex flex-col border-r border-slate-700">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl font-bold">Video-Matic</h1>
      </div>
      <div className="flex-1 p-4 space-y-2">
        {links.map((link) => {
          const active = isActive(link.href)
          const Icon = link.icon
          return (
            <motion.div key={link.href} whileHover={{ x: 4 }}>
              <Link to={link.href}>
                <Button
                  variant={active ? 'default' : 'ghost'}
                  className={`w-full justify-start ${
                    active
                      ? 'bg-[#229ED9] hover:bg-[#1a7aaf] text-white'
                      : 'text-gray-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {link.label}
                </Button>
              </Link>
            </motion.div>
          )
        })}
      </div>
    </nav>
  )
}
