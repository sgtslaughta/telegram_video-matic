import { Link } from 'react-router-dom'

export default function Sidebar() {
  const links = [
    { label: 'Dashboard', href: '/' },
    { label: 'Subscriptions', href: '/subscriptions' },
    { label: 'Browse', href: '/browse' },
    { label: 'Activity', href: '/activity' },
    { label: 'Settings', href: '/settings' },
  ]

  return (
    <nav className="w-64 h-screen bg-slate-900 text-white overflow-y-auto flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl font-bold">Video-Matic</h1>
      </div>
      <div className="flex-1 p-4 space-y-2">
        {links.map((link) => (
          <Link
            key={link.href}
            to={link.href}
            className="block px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            {link.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
