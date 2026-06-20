import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function Sidebar() {
  const location = useLocation()
  const links = [
    { label: 'Dashboard', href: '/' },
    { label: 'Subscriptions', href: '/subscriptions' },
    { label: 'Browse', href: '/browse' },
    { label: 'Activity', href: '/activity' },
    { label: 'Settings', href: '/settings' },
  ]

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(href)
  }

  return (
    <nav className="w-64 h-screen bg-slate-900 text-white overflow-y-auto flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl font-bold">Video-Matic</h1>
      </div>
      <div className="flex-1 p-4 space-y-2">
        {links.map((link) => {
          const active = isActive(link.href)
          return (
            <motion.div key={link.href} whileHover={{ x: 4 }}>
              <Link
                to={link.href}
                className={`block px-4 py-2 rounded-lg transition-all ${
                  active
                    ? 'bg-[#229ED9] text-white font-semibold shadow-lg'
                    : 'hover:bg-slate-800 text-gray-300'
                }`}
              >
                {link.label}
              </Link>
            </motion.div>
          )
        })}
      </div>
    </nav>
  )
}
